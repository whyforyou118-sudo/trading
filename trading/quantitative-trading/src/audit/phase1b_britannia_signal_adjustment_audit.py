"""Compare raw momentum with point-in-time Britannia signal adjustments.

This is a signal-only audit. It does not calculate portfolio performance,
overwrite the existing selection evidence, or authorize Run 1.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data.prices import ManifestPriceStore, load_raw_instrument_close_by_isin
from strategy.corporate_action_signal import (
    BRITANNIA_DEBENTURE_EVENTS,
    adjust_signal_price_maps,
)
from strategy.momentum import Member
from strategy.selection import build_quarterly_selection_audit


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty audit: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_listing_quotes(
    root: Path,
    manifest_rows: list[dict[str, str]],
) -> tuple[dict[str, float], list[str]]:
    manifest_by_date = {row.get("date", ""): row for row in manifest_rows}
    quotes: dict[str, float] = {}
    failures: list[str] = []
    for event in BRITANNIA_DEBENTURE_EVENTS:
        listing_date = event.first_tradable_date.isoformat()
        manifest_row = manifest_by_date.get(listing_date)
        if manifest_row is None:
            failures.append(f"MISSING_MANIFEST_DATE:{event.event_id}:{listing_date}")
            continue
        path = root / manifest_row["format"] / Path(manifest_row["url"]).name
        if not path.exists():
            failures.append(f"MISSING_RAW_FILE:{event.event_id}:{path}")
            continue
        try:
            quotes[event.event_id] = load_raw_instrument_close_by_isin(
                path, event.isin, event.first_tradable_date
            )
        except (ValueError, OSError) as exc:
            failures.append(f"LISTING_QUOTE_UNAVAILABLE:{event.event_id}:{exc}")
    return quotes, failures


def selection_by_date(selections):
    return {
        row.decision_date.isoformat(): row
        for row in selections
    }


def selected_symbols(row) -> list[str]:
    return [symbol for symbol, _, _ in row.ranked_candidates[:5]]


def main() -> int:
    calendar_path = ROOT / "audits" / "nse_trading_calendar_v3.csv"
    manifest_path = ROOT / "data" / "raw" / "prices" / "download_manifest.csv"
    price_root = ROOT / "data" / "raw" / "prices"
    baseline_path = ROOT / "data" / "reference" / "nifty50_baseline.csv"
    transitions_path = ROOT / "data" / "reference" / "nifty50_membership.csv"
    events_path = ROOT / "data" / "reference" / "security_identity_events.csv"
    pit_path = ROOT / "audits" / "phase1a_pit_decision_table.csv"
    existing_selection_path = ROOT / "audits" / "phase1b_selection_audit.csv"

    required = [
        calendar_path, manifest_path, baseline_path, transitions_path,
        events_path, pit_path, existing_selection_path,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("BLOCKED: required local signal-audit inputs are missing:")
        print("\n".join(missing))
        return 2

    def load(path: Path) -> list[dict[str, str]]:
        return read_csv(path)

    sessions = [
        date.fromisoformat(row["date"])
        for row in load(calendar_path)
        if row.get("is_trading_day", "").strip().lower() == "true"
    ]
    baseline = [
        Member(row["symbol"], row["company_name"], row["isin"])
        for row in load(baseline_path)
    ]
    transitions = load(transitions_path)
    identity_events = load(events_path)
    pit_rows = load(pit_path)
    decisions = sorted({date.fromisoformat(row["decision_date"]) for row in pit_rows})
    manifest_rows = load(manifest_path)
    store = ManifestPriceStore(price_root, manifest_rows)

    parent_ex_date_closes: dict[str, float] = {}
    for event in BRITANNIA_DEBENTURE_EVENTS:
        try:
            ex_prices = store.prices(event.ex_date)
            parent = ex_prices.get(event.symbol)
            if parent is None:
                raise ValueError(f"MISSING_RAW_PARENT_EQUITY_CLOSE:{event.event_id}")
            parent_ex_date_closes[event.event_id] = float(parent.close)
        except (KeyError, FileNotFoundError, ValueError) as exc:
            print(f"BLOCKED: cannot establish raw parent ex-date close: {exc}")
            return 2

    listing_quotes, listing_quote_failures = load_listing_quotes(price_root, manifest_rows)

    common = dict(
        trading_dates=sessions,
        price_store=store,
        baseline=baseline,
        transitions=transitions,
        identity_events=identity_events,
        start=date(2018, 1, 1),
        end=date(2025, 12, 31),
        formation_months=12,
        skip_months=1,
        holdings=5,
        decision_dates=decisions,
    )

    raw = build_quarterly_selection_audit(**common)

    adjustment_log: list[dict[str, object]] = []

    def make_adjuster(policy: str):
        def adjuster(formation_end, start_prices, end_prices):
            start_adjusted, end_adjusted, event_log = adjust_signal_price_maps(
                formation_end,
                start_prices,
                end_prices,
                policy=policy,
                parent_ex_date_closes=parent_ex_date_closes,
                listing_debenture_closes=listing_quotes,
            )
            for row in event_log:
                adjustment_log.append(dict(row))
            return start_adjusted, end_adjusted
        return adjuster

    primary = build_quarterly_selection_audit(
        **common,
        signal_price_adjuster=make_adjuster("provisional_face_value"),
    )

    listing_only = None
    if not listing_quote_failures:
        listing_only = build_quarterly_selection_audit(
            **common,
            signal_price_adjuster=make_adjuster("listing_only"),
        )

    raw_by_date = selection_by_date(raw)
    primary_by_date = selection_by_date(primary)
    listing_by_date = selection_by_date(listing_only) if listing_only is not None else {}

    existing = load(existing_selection_path)
    existing_selected: dict[str, list[str]] = {}
    for row in existing:
        if row.get("selection_status") == "PASS":
            existing_selected.setdefault(row["decision_date"], []).append(row["symbol"])
    raw_artifact_match = True
    raw_artifact_mismatches = []
    for decision in sorted(raw_by_date):
        expected = existing_selected.get(decision, [])
        actual = selected_symbols(raw_by_date[decision])
        if expected != actual:
            raw_artifact_match = False
            raw_artifact_mismatches.append({
                "decision_date": decision,
                "existing_symbols": "|".join(expected),
                "recomputed_raw_symbols": "|".join(actual),
            })

    comparison_rows: list[dict[str, object]] = []
    decision_summary: list[dict[str, object]] = []
    for decision in sorted(raw_by_date):
        raw_row = raw_by_date[decision]
        primary_row = primary_by_date[decision]
        raw_ranks = {
            symbol: (score, rank)
            for symbol, score, rank in raw_row.ranked_candidates
        }
        primary_ranks = {
            symbol: (score, rank)
            for symbol, score, rank in primary_row.ranked_candidates
        }
        listing_ranks = {
            symbol: (score, rank)
            for symbol, score, rank in listing_by_date[decision].ranked_candidates
        } if listing_only is not None else {}
        all_symbols = sorted(set(raw_ranks) | set(primary_ranks) | set(listing_ranks))
        for symbol in all_symbols:
            raw_score, raw_rank = raw_ranks.get(symbol, (None, None))
            primary_score, primary_rank = primary_ranks.get(symbol, (None, None))
            listing_score, listing_rank = listing_ranks.get(symbol, (None, None))
            comparison_rows.append({
                "decision_date": decision,
                "formation_start": raw_row.formation_start.isoformat(),
                "formation_end": raw_row.formation_end.isoformat(),
                "symbol": symbol,
                "raw_score": raw_score,
                "raw_rank": raw_rank,
                "primary_face_value_score": primary_score,
                "primary_face_value_rank": primary_rank,
                "primary_selected_top5": primary_rank is not None and primary_rank <= 5,
                "listing_only_score": listing_score,
                "listing_only_rank": listing_rank,
                "listing_only_selected_top5": listing_rank is not None and listing_rank <= 5,
            })
        raw_symbols = selected_symbols(raw_row)
        primary_symbols = selected_symbols(primary_row)
        listing_symbols = selected_symbols(listing_by_date[decision]) if listing_only is not None else []
        decision_summary.append({
            "decision_date": decision,
            "formation_start": raw_row.formation_start.isoformat(),
            "formation_end": raw_row.formation_end.isoformat(),
            "raw_top5": "|".join(raw_symbols),
            "primary_face_value_top5": "|".join(primary_symbols),
            "primary_changed_names_vs_raw": sum(a != b for a, b in zip(raw_symbols, primary_symbols)),
            "primary_overlap_count": len(set(raw_symbols) & set(primary_symbols)),
            "listing_only_top5": "|".join(listing_symbols),
            "listing_only_changed_names_vs_raw": (
                sum(a != b for a, b in zip(raw_symbols, listing_symbols))
                if listing_only is not None else ""
            ),
            "listing_only_overlap_count": (
                len(set(raw_symbols) & set(listing_symbols)) if listing_only is not None else ""
            ),
        })

    comparison_path = ROOT / "audits" / "phase1b_britannia_signal_adjustment_comparison.csv"
    summary_path = ROOT / "audits" / "phase1b_britannia_signal_adjustment_summary.csv"
    adjustment_path = ROOT / "audits" / "phase1b_britannia_signal_adjustment_events.csv"
    write_csv(comparison_path, comparison_rows)
    write_csv(summary_path, decision_summary)
    if adjustment_log:
        write_csv(adjustment_path, adjustment_log)

    summary = {
        "audit_type": "POINT_IN_TIME_CORPORATE_ACTION_SIGNAL_ADJUSTMENT_NOT_PERFORMANCE",
        "strategy": "Frozen V6 PIT NIFTY 50, 12M formation, 1M skip, Top-5, quarterly",
        "decision_dates": len(decisions),
        "primary_policy": "PROVISIONAL_FACE_VALUE",
        "primary_adjustment_status": "PASS",
        "listing_only_sensitivity_status": "PASS" if listing_only is not None else "BLOCKED",
        "listing_quote_failures": listing_quote_failures,
        "raw_selection_artifact_match": raw_artifact_match,
        "raw_selection_artifact_mismatches": raw_artifact_mismatches,
        "primary_top5_changed_decisions_vs_raw": sum(
            decision_summary_row["raw_top5"] != decision_summary_row["primary_face_value_top5"]
            for decision_summary_row in decision_summary
        ),
        "listing_only_top5_changed_decisions_vs_raw": (
            sum(
                decision_summary_row["raw_top5"] != decision_summary_row["listing_only_top5"]
                for decision_summary_row in decision_summary
            ) if listing_only is not None else None
        ),
        "adjustment_event_log_rows": len(adjustment_log),
        "outputs": [
            str(comparison_path.relative_to(ROOT)),
            str(summary_path.relative_to(ROOT)),
            str(adjustment_path.relative_to(ROOT)) if adjustment_path.exists() else None,
        ],
        "run1_authorized": False,
        "limitations": [
            "The primary signal adjustment uses provisional face value, not verified fair value.",
            "The listing-only sensitivity uses raw close by ISIN on the first tradable date and applies no adjustment before that quote is observable.",
            "The existing frozen selection artifacts are not overwritten.",
            "A passing signal audit does not authorize historical performance Run 1.",
        ],
        "status": (
            "PASS"
            if raw_artifact_match and listing_only is not None
            else "BLOCKED"
        ),
    }
    output_json = ROOT / "audits" / "phase1b_britannia_signal_adjustment_summary.json"
    output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
