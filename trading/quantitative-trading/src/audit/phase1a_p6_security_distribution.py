"""Audit the Britannia bonus-debenture scheme path condition.

The scheme is deliberately not treated as an equity bonus. This audit verifies
the two NSE corporate-action rows and proves whether the frozen V6 Top-5 path
could have held BRITANNIA at either entitlement date.

If BRITANNIA was not selected by the strategy at either entitlement date, the
separate debenture distribution is path-conditionally irrelevant to the V6
portfolio and no debenture market-value model is required for this path.

The audit fails closed if BRITANNIA is selected on or before either entitlement
date.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CA = ROOT / "data/raw/corporate_actions/nse_corporate_actions_2018_2025.csv"
PIT = ROOT / "audits/phase1a_pit_decision_table.csv"

EXPECTED = {
    ("BRITANNIA", "22-Aug-2019"),
    ("BRITANNIA", "25-May-2021"),
}

EVENT_DATES = (
    date(2019, 8, 22),
    date(2021, 5, 25),
)

KEYWORDS = ("debenture", "scheme")


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def main() -> int:
    if not CA.exists():
        raise SystemExit(f"BLOCKED: missing {CA}")

    if not PIT.exists():
        raise SystemExit(f"BLOCKED: missing {PIT}")

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
        print(
            "STATUS: BLOCKED — expected Britannia scheme rows "
            "not fully present."
        )
        return 1

    with PIT.open("r", encoding="utf-8-sig", newline="") as f:
        pit_rows = list(csv.DictReader(f))

    britannia_rows = []
    for row in pit_rows:
        if row.get("symbol", "").strip().upper() != "BRITANNIA":
            continue

        decision_date = parse_iso_date(row["decision_date"])

        if row.get("eligible", "").strip().lower() != "true":
            continue

        britannia_rows.append(
            {
                "decision_date": decision_date,
                "execution_date": row.get("execution_date", "").strip(),
            }
        )

    if not britannia_rows:
        print("BRITANNIA V6 selections: none")
        print(
            "STATUS: BLOCKED — PIT decision table contains no "
            "BRITANNIA selection to establish path."
        )
        return 2

    britannia_rows.sort(key=lambda x: x["decision_date"])

    print(f"BRITANNIA V6 selections: {len(britannia_rows)}")

    first_selection = britannia_rows[0]
    print(
        "First V6 BRITANNIA selection: "
        f"{first_selection['decision_date'].isoformat()} "
        f"(execution {first_selection['execution_date']})"
    )

    failures = []

    for event_date in EVENT_DATES:
        prior_or_same = [
            row
            for row in britannia_rows
            if row["decision_date"] <= event_date
        ]

        if prior_or_same:
            print(
                f"BLOCKED — BRITANNIA selected on/before "
                f"{event_date.isoformat()}: "
                f"{prior_or_same}"
            )
            failures.append(event_date)
        else:
            print(
                f"PASS — no V6 BRITANNIA selection on/before "
                f"{event_date.isoformat()}"
            )

    print(
        "Treatment: separate 5.5% unsecured, non-convertible, "
        "redeemable debenture; not an equity bonus."
    )

    if failures:
        print(
            "STATUS: BLOCKED — Britannia debenture entitlement may be "
            "path-relevant and requires auditable treatment."
        )
        return 3

    print(
        "STATUS: PASS — Britannia debenture distributions are "
        "path-conditionally irrelevant to the frozen V6 portfolio."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
