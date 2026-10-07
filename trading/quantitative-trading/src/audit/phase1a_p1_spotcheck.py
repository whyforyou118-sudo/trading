"""P1 — generate and validate the three-date human spot-check artifact.

This gate intentionally requires human confirmation from raw/source records.
The script never turns expected-vs-expected agreement into a human PASS.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPRO = ROOT / "audits/phase1a_gate4_reproduction.csv"
OUT = ROOT / "audits/phase1a_p1_human_spotcheck.csv"

FIELDS = [
    "decision_date",
    "rank1",
    "rank2",
    "rank3",
    "rank4",
    "rank5",
    "raw_source_checked",
    "signal_recomputed",
    "execution_open_checked",
    "holdings_checked",
    "reviewer",
    "status",
    "notes",
]


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def generate_template() -> list[dict[str, str]]:
    rows = read(REPRO)
    dates = sorted({r["rebalance_date"] for r in rows})
    if len(dates) < 3:
        raise RuntimeError("P1 requires at least three frozen decision dates")

    chosen = [dates[0], dates[len(dates) // 2], dates[-1]]
    result = []
    for date in chosen:
        ranked = {
            int(r["rank"]): r["reference_symbol"]
            for r in rows
            if r["rebalance_date"] == date
        }
        if set(ranked) != {1, 2, 3, 4, 5}:
            raise RuntimeError(f"incomplete Top-5 reproduction for {date}")
        result.append({
            "decision_date": date,
            "rank1": ranked[1],
            "rank2": ranked[2],
            "rank3": ranked[3],
            "rank4": ranked[4],
            "rank5": ranked[5],
            "raw_source_checked": "",
            "signal_recomputed": "",
            "execution_open_checked": "",
            "holdings_checked": "",
            "reviewer": "",
            "status": "PENDING_HUMAN_REVIEW",
            "notes": "",
        })
    return result


def main() -> int:
    if not REPRO.exists():
        print("BLOCKED: G4 reproduction artifact missing")
        return 1

    if not OUT.exists():
        rows = generate_template()
        with OUT.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Created human-review template: {OUT}")
        print("STATUS: BLOCKED — human verification is required.")
        return 1

    rows = read(OUT)
    if len(rows) != 3:
        print("STATUS: BLOCKED — P1 requires exactly three reviewed dates.")
        return 1

    required_yes = {"YES", "TRUE", "PASS"}
    failures = []
    for row in rows:
        if row.get("status", "").upper() != "PASS":
            failures.append(f"{row.get('decision_date')}: status is not PASS")
        for field in (
            "raw_source_checked",
            "signal_recomputed",
            "execution_open_checked",
            "holdings_checked",
        ):
            if row.get(field, "").strip().upper() not in required_yes:
                failures.append(f"{row.get('decision_date')}: {field} not confirmed")
        if not row.get("reviewer", "").strip():
            failures.append(f"{row.get('decision_date')}: reviewer missing")

    print("PHASE 1A P1 — HUMAN SPOT-CHECK")
    print(f"Reviewed dates: {len(rows)}")
    print(f"Failures: {len(failures)}")
    print(f"Artifact: {OUT}")
    if failures:
        for failure in failures:
            print("BLOCKED:", failure)
        return 1

    print("STATUS: PASS — three dates explicitly reviewed by a human.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
