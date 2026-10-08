"""P1 — data-verified three-date spot-check.

This gate verifies the frozen decision dates using repository evidence.
It does not claim human attestation.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REPRO = ROOT / "audits/phase1a_gate4_reproduction.csv"
TOP5 = ROOT / "audits/phase05_top5_feasibility.csv"
CAPITAL = ROOT / "audits/phase05_capital_feasibility.csv"

REQUIRED_DATES = [
    "2018-03-28",
    "2021-12-31",
    "2025-09-30",
]


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    failures = []

    for path in (REPRO, TOP5, CAPITAL):
        if not path.exists():
            failures.append(f"missing artifact: {path}")

    if failures:
        print("PHASE 1A P1 — DATA VERIFICATION")
        for x in failures:
            print("BLOCKED:", x)
        return 1

    repro = read(REPRO)
    top5 = read(TOP5)
    capital = read(CAPITAL)

    for date in REQUIRED_DATES:
        r = [
            x for x in repro
            if x["rebalance_date"] == date
            and x["status"].upper() == "PASS"
        ]

        if len(r) != 5:
            failures.append(
                f"{date}: expected 5 PASS G4 rows, found {len(r)}"
            )

        t = [x for x in top5 if x["rebalance_date"] == date]

        if len(t) != 5:
            failures.append(
                f"{date}: expected 5 Top-5 feasibility rows, found {len(t)}"
            )

        else:
            if any(x["price_basis"] != "RAW_UNADJUSTED" for x in t):
                failures.append(
                    f"{date}: non-RAW_UNADJUSTED execution price found"
                )

            if any(not x["execution_price"] for x in t):
                failures.append(
                    f"{date}: missing execution price"
                )

    for date in REQUIRED_DATES:
        rows = [x for x in capital if x["rebalance_date"] == date]

        primary = [
            x for x in rows
            if float(x["capital"]) == 25000
        ]

        if len(primary) != 1:
            failures.append(
                f"{date}: ₹25,000 capital feasibility row missing"
            )
            continue

        row = primary[0]

        if row["status"].upper() != "PASS":
            failures.append(
                f"{date}: capital feasibility is not PASS"
            )

        if int(row["selected_count"]) != 5:
            failures.append(
                f"{date}: selected_count != 5"
            )

        if float(row["cash_after_allocation"]) < 0:
            failures.append(
                f"{date}: negative residual cash"
            )

    print("PHASE 1A P1 — DATA VERIFICATION")
    print("Dates checked:", len(REQUIRED_DATES))
    print("Failures:", len(failures))

    if failures:
        for failure in failures:
            print("BLOCKED:", failure)
        return 1

    print("2018-03-28: PASS")
    print("2021-12-31: PASS")
    print("2025-09-30: PASS")
    print("STATUS: PASS — data evidence verifies all three P1 spot-check dates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())