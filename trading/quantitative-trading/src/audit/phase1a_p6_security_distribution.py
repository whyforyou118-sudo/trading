"""Audit the Britannia bonus-debenture scheme blockers.

The scheme is deliberately not treated as an equity bonus. This script verifies
the two NSE corporate-action rows and records the production blocker until an
auditable market-value treatment for the separate debenture security exists.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CA = ROOT / "data/raw/corporate_actions/nse_corporate_actions_2018_2025.csv"

EXPECTED = {
    ("BRITANNIA", "22-Aug-2019"),
    ("BRITANNIA", "25-May-2021"),
}

KEYWORDS = ("debenture", "scheme")

def main() -> int:
    if not CA.exists():
        raise SystemExit(f"BLOCKED: missing {CA}")

    with CA.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    found = []
    for row in rows:
        key = (
            row.get("symbol", "").strip().upper(),
            row.get("exDate", "").strip(),
        )
        subject = row.get("subject", "").strip().lower()
        if key in EXPECTED and all(k in subject for k in KEYWORDS):
            found.append((key[0], key[1], row.get("subject", "")))

    print("PHASE 1A P6 — SECURITY DISTRIBUTION AUDIT")
    print(f"Expected scheme rows: {len(EXPECTED)}")
    print(f"Matched NSE rows: {len(found)}")
    for row in sorted(found):
        print(" | ".join(row))

    if len(found) != len(EXPECTED):
        print("STATUS: BLOCKED — expected Britannia scheme rows not fully present.")
        return 1

    print("Treatment: separate 5.5% unsecured, non-convertible, redeemable debenture; not an equity bonus.")
    print("STATUS: BLOCKED — market-value/entitlement treatment is not yet implemented.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
