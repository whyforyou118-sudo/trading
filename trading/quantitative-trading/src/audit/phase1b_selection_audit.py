"""Run a non-performance quarterly V6 selection audit and reconcile frozen evidence.

This command reads the locally downloaded raw NSE price archive. It does not
calculate portfolio returns, execute trades, or authorize the historical Run 1.
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

from data.prices import ManifestPriceStore
from strategy.momentum import Member
from strategy.selection import build_quarterly_selection_audit


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty audit: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    calendar_path = ROOT / "audits" / "nse_trading_calendar_v3.csv"
    manifest_path = ROOT / "data" / "raw" / "prices" / "download_manifest.csv"
    price_root = ROOT / "data" / "raw" / "prices"
    baseline_path = ROOT / "data" / "reference" / "nifty50_baseline.csv"
    transitions_path = ROOT / "data" / "reference" / "nifty50_membership.csv"
    events_path = ROOT / "data" / "reference" / "security_identity_events.csv"
    phase05_path = ROOT / "audits" / "phase05_top5_feasibility.csv"
    pit_path = ROOT / "audits" / "phase1a_pit_decision_table.csv"

    required = [
        calendar_path, manifest_path, baseline_path, transitions_path,
        events_path, phase05_path, pit_path,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("BLOCKED: required local audit inputs are missing:")
        print("\n".join(missing))
        return 2

    sessions = [
        date.fromisoformat(r["date"])
        for r in read_csv(calendar_path)
        if r.get("is_trading_day", "").strip().lower() == "true"
    ]
    baseline = [
        Member(r["symbol"], r["company_name"], r["isin"])
        for r in read_csv(baseline_path)
    ]
    transitions = read_csv(transitions_path)
    events = read_csv(events_path)
    store = ManifestPriceStore.from_manifest(price_root, manifest_path)

    selections = build_quarterly_selection_audit(
        trading_dates=sessions,
        price_store=store,
        baseline=baseline,
        transitions=transitions,
        identity_events=events,
        start=date(2018, 1, 1),
        end=date(2025, 12, 31),
        formation_months=12,
        skip_months=1,
        holdings=5,
    )

    selection_rows: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    for row in selections:
        coverage_rows.append({
            "decision_date": row.decision_date.isoformat(),
            "formation_start": row.formation_start.isoformat(),
            "formation_end": row.formation_end.isoformat(),
            "execution_date": row.execution_date.isoformat(),
            "member_count": row.member_count,
            "signal_eligible_count": row.signal_eligible_count,
            "selected_count": len(row.selected_symbols),
            "selected_symbols": "|".join(row.selected_symbols),
            "missing_execution_opens": "|".join(row.missing_execution_opens),
            "status": row.status,
            "reason": row.reason,
        })
        by_symbol = {symbol: (score, rank) for symbol, score, rank in row.ranked_candidates}
        for symbol in row.selected_symbols:
            score, rank = by_symbol[symbol]
            selection_rows.append({
                "decision_date": row.decision_date.isoformat(),
                "execution_date": row.execution_date.isoformat(),
                "rank": rank,
                "symbol": symbol,
                "momentum_raw_unadjusted": f"{score:.15g}",
                "price_basis": "RAW_UNADJUSTED",
                "execution_open_available": symbol not in row.missing_execution_opens,
                "selection_status": row.status,
            })

    selection_path = ROOT / "audits" / "phase1b_selection_audit.csv"
    coverage_path = ROOT / "audits" / "phase1b_selection_coverage.csv"
    write_csv(selection_path, selection_rows)
    write_csv(coverage_path, coverage_rows)

    # Reconcile selected names and execution dates against both frozen evidence
    # tables. Do not use either table to alter the new implementation's output.
    expected_by_source: dict[str, dict[str, dict[str, object]]] = {}
    for source, path in (("phase05", phase05_path), ("phase1a_pit", pit_path)):
        raw_rows = read_csv(path)
        grouped: dict[str, dict[str, object]] = {}
        for row in raw_rows:
            d = row.get("rebalance_date") or row.get("decision_date") or ""
            symbol = row.get("symbol", "")
            if not d or not symbol:
                continue
            execution = row.get("execution_date", "")
            if d not in grouped:
                grouped[d] = {"symbols": [], "execution_dates": set()}
            symbols = grouped[d]["symbols"]
            assert isinstance(symbols, list)
            if symbol not in symbols:
                symbols.append(symbol)
            if execution:
                execution_dates = grouped[d]["execution_dates"]
                assert isinstance(execution_dates, set)
                execution_dates.add(execution)
        # Phase 0.5 has explicit rank values; use them rather than trusting file order.
        if source == "phase05":
            for d in grouped:
                ranks = {
                    row["symbol"]: int(row["rank"])
                    for row in raw_rows
                    if (row.get("rebalance_date") or "") == d
                    and row.get("symbol") and row.get("rank", "").isdigit()
                }
                symbols = grouped[d]["symbols"]
                assert isinstance(symbols, list)
                symbols.sort(key=lambda symbol: ranks.get(symbol, 10**9))
        expected_by_source[source] = grouped

    reconciliation_rows: list[dict[str, object]] = []
    for source, grouped in expected_by_source.items():
        actual_dates = {r.decision_date.isoformat(): r for r in selections}
        all_dates = sorted(set(grouped) | set(actual_dates))
        for d in all_dates:
            expected = grouped.get(d, {"symbols": [], "execution_dates": set()})
            expected_symbols = list(expected["symbols"])
            expected_exec_dates = expected["execution_dates"]
            actual = actual_dates.get(d)
            actual_symbols = list(actual.selected_symbols) if actual else []
            actual_exec = actual.execution_date.isoformat() if actual else ""
            expected_exec = "|".join(sorted(expected_exec_dates))
            missing_expected = [s for s in expected_symbols if s not in actual_symbols]
            unexpected_actual = [s for s in actual_symbols if s not in expected_symbols]
            date_match = (
                not expected_exec_dates or expected_exec_dates == {actual_exec}
            ) if actual else False
            symbols_match = expected_symbols == actual_symbols
            reconciliation_rows.append({
                "source": source,
                "decision_date": d,
                "expected_count": len(expected_symbols),
                "actual_count": len(actual_symbols),
                "expected_symbols": "|".join(expected_symbols),
                "actual_symbols": "|".join(actual_symbols),
                "missing_expected": "|".join(missing_expected),
                "unexpected_actual": "|".join(unexpected_actual),
                "expected_execution_dates": expected_exec,
                "actual_execution_date": actual_exec,
                "symbols_match": symbols_match,
                "execution_date_match": date_match,
                "status": "PASS" if symbols_match and date_match else "MISMATCH",
            })

    reconciliation_path = ROOT / "audits" / "phase1b_selection_reconciliation.csv"
    write_csv(reconciliation_path, reconciliation_rows)
    mismatch_count = sum(r["status"] != "PASS" for r in reconciliation_rows)
    summary = {
        "audit_type": "SIGNAL_SELECTION_ONLY_NOT_PERFORMANCE",
        "quarterly_decision_count": len(selections),
        "blocked_decision_count": sum(r.status == "BLOCKED" for r in selections),
        "reconciliation_rows": len(reconciliation_rows),
        "mismatch_count": mismatch_count,
        "status": "PASS" if mismatch_count == 0 else "MISMATCH_REQUIRES_REVIEW",
        "run1_authorized": False,
        "outputs": [
            str(selection_path.relative_to(ROOT)),
            str(coverage_path.relative_to(ROOT)),
            str(reconciliation_path.relative_to(ROOT)),
        ],
    }
    summary_path = ROOT / "audits" / "phase1b_selection_reconciliation.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if mismatch_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
