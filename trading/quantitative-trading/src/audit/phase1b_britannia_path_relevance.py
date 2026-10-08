"""Path-conditional audit for Britannia debenture events in frozen V6.

This audit determines whether the frozen Top-5 strategy had an eligible
BRITANNIA position at either debenture entitlement date, and whether either
ex-date falls inside any quarterly decision's 12M formation window after
the 1M skip. It does not estimate coupon cashflows or authorize Run 1.
"""
from __future__ import annotations

import csv
import json
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping


EVENTS = (
    {
        "event_id": "BRITANNIA_2019_BONUS_DEBENTURE",
        "ex_date": "2019-08-22",
        "first_tradable_date": "2019-10-09",
        "redemption_date": "2022-08-26",
    },
    {
        "event_id": "BRITANNIA_2021_BONUS_DEBENTURE",
        "ex_date": "2021-05-25",
        "first_tradable_date": "2021-07-20",
        "redemption_date": "2024-06-03",
    },
)


def _subtract_months(value: date, months: int) -> date:
    """Subtract calendar months, clamping to the destination month's last day."""
    month_index = value.year * 12 + (value.month - 1) - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def _load_rows(
    path: Path,
    required_columns: set[str] | None = None,
) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = required_columns or {
        "decision_date", "execution_date", "symbol", "selection_status"
    }
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"selection audit missing required columns: {sorted(required)}")
    return rows


def build_path_relevance_report(
    rows: Iterable[Mapping[str, str]],
    coverage_rows: Iterable[Mapping[str, str]] | None = None,
) -> dict:
    rows = list(rows)
    coverage_rows = list(coverage_rows) if coverage_rows is not None else None
    selections = [
        row for row in rows
        if row.get("selection_status") == "PASS"
        and row.get("symbol", "").strip().upper() == "BRITANNIA"
    ]
    parsed = []
    for row in selections:
        parsed.append({
            "decision_date": date.fromisoformat(row["decision_date"]),
            "execution_date": date.fromisoformat(row["execution_date"]),
        })
    parsed.sort(key=lambda row: row["decision_date"])
    first_execution = parsed[0]["execution_date"].isoformat() if parsed else None
    # The selection audit contains five rows per decision date. Use every
    # unique date, not only dates when BRITANNIA made the Top-5: a corporate
    # action can change its momentum rank even when it is not selected.
    if coverage_rows is not None:
        required_coverage = {"decision_date", "formation_start", "formation_end"}
        if not coverage_rows or not required_coverage.issubset(coverage_rows[0]):
            raise ValueError("coverage audit missing decision_date/formation_start/formation_end")
        windows = {
            date.fromisoformat(row["decision_date"]): (
                date.fromisoformat(row["formation_start"]),
                date.fromisoformat(row["formation_end"]),
            )
            for row in coverage_rows
        }
        if len(windows) != len(coverage_rows):
            raise ValueError("coverage audit contains duplicate decision dates")
        window_source = "phase1b_selection_coverage.csv"
    else:
        # Synthetic unit tests may provide only decision dates. Production audit
        # must use exact, calendar-derived formation dates from coverage output.
        windows = {}
        for decision_date in sorted({date.fromisoformat(row["decision_date"]) for row in rows}):
            signal_end = _subtract_months(decision_date, 1)
            windows[decision_date] = (_subtract_months(signal_end, 12), signal_end)
        window_source = "derived_from_synthetic_decision_dates"
    decision_dates = sorted(windows)
    if not decision_dates:
        raise ValueError("selection audit contains no decision dates")

    event_results = []
    all_pass = True
    for event in EVENTS:
        ex_date = date.fromisoformat(event["ex_date"])
        held_before_ex_date = any(item["execution_date"] <= ex_date for item in parsed)
        lookback_overlaps = []
        for decision_date in decision_dates:
            # Production uses exact month-end dates from the selection coverage artifact.
            signal_start, signal_end = windows[decision_date]
            if signal_start <= ex_date <= signal_end:
                lookback_overlaps.append({
                    "decision_date": decision_date.isoformat(),
                    "formation_start": signal_start.isoformat(),
                    "formation_end": signal_end.isoformat(),
                })
        passed = not held_before_ex_date and not lookback_overlaps
        all_pass = all_pass and passed
        event_results.append({
            **event,
            "eligible_parent_position_at_ex_date": held_before_ex_date,
            "ex_date_in_any_quarterly_signal_formation_window": bool(lookback_overlaps),
            "overlapping_signal_windows": lookback_overlaps,
            "path_conditionally_irrelevant_to_frozen_V6": passed,
            "status": "PASS" if passed else "BLOCKED",
        })

    return {
        "audit_type": "PATH_CONDITIONAL_CORPORATE_ACTION_RELEVANCE_NOT_PERFORMANCE",
        "strategy": "V6 frozen PIT NIFTY 50 Top-5, 12M formation, 1M skip, quarterly",
        "selection_rows_checked": sum(
            1 for row in rows if row.get("selection_status") == "PASS"
        ),
        "quarterly_decision_dates_checked": len(decision_dates),
        "formation_window_source": window_source,
        "BRITANNIA_selection_count": len(parsed),
        "first_BRITANNIA_execution_date": first_execution,
        "events": event_results,
        "status": "PASS" if all_pass else "BLOCKED",
        "run1_authorized": False,
        "limitations": [
            "This checks signal-window relevance using all unique decision dates in the supplied frozen selection audit.",
            "It does not verify debenture coupon amounts or replace the synthetic accounting tests.",
            "It does not authorize historical performance Run 1; all other preflight gates remain required.",
        ],
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    input_path = root / "audits" / "phase1b_selection_audit.csv"
    output_path = root / "audits" / "phase1b_britannia_path_relevance.json"
    coverage_path = ROOT / "audits" / "phase1b_selection_coverage.csv"
    if not coverage_path.exists():
        raise SystemExit(f"BLOCKED: missing exact formation-window artifact: {coverage_path}")
    report = build_path_relevance_report(
        _load_rows(input_path),
        _load_rows(coverage_path, {"decision_date", "formation_start", "formation_end"}),
    )
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
