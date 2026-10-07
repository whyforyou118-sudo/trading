"""P2 — truncation-invariance checker.

Compare a decision artifact generated with data truncated at each decision date
against the corresponding full-data decision artifact. The checker is exact:
membership, signal-source date, execution date, rank and selected symbol must
match. It does not run performance.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / "audits/phase1a_pit_decision_table.csv"
TRUNCATED = ROOT / "audits/phase1a_p2_truncated_decision_table.csv"
OUT = ROOT / "audits/phase1a_p2_truncation_report.csv"

KEYS = (
    "decision_date",
    "symbol",
    "signal_source_date",
    "execution_date",
)


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def canonical(rows):
    return sorted(
        tuple(r.get(k, "") for k in KEYS)
        for r in rows
    )


def main() -> int:
    if not FULL.exists() or not TRUNCATED.exists():
        print("STATUS: BLOCKED — both full and per-decision truncated artifacts are required.")
        return 1

    full = canonical(read(FULL))
    truncated = canonical(read(TRUNCATED))

    status = "PASS" if full == truncated else "FAIL"
    detail = "exact equality" if status == "PASS" else "decision artifacts differ"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerow({
            "check": "truncation_invariance",
            "status": status,
            "detail": detail,
        })

    print("PHASE 1A P2 — TRUNCATION INVARIANCE")
    print(f"Full rows: {len(full)}")
    print(f"Truncated rows: {len(truncated)}")
    print(f"Status: {status}")
    if status != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
