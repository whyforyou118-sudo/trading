"""Audit the three rights events relevant to the frozen V6 signal path.

This is a treatment audit, not a performance adjustment engine. It records the
NSE rights ratio/issue price from the corporate-action subject. No production
adjustment factor is persisted by this script.
"""
from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CA = ROOT / "data/raw/corporate_actions/nse_corporate_actions_2018_2025.csv"

TARGETS = {
    ("GRASIM", "2024-01-10"),
    ("TATACONSUM", "2024-07-26"),
    ("ADANIENT", "2025-11-17"),
}

PATTERN = re.compile(
    r"Rights\s+(?P<a>\d+)\s*:\s*(?P<b>\d+)\s*@\s*Premium\s+Rs\s*(?P<p>[0-9.]+)",
    re.I,
)


def normalize_nse_date(value: str) -> str:
    value = value.strip()
    return datetime.strptime(value, "%d-%b-%Y").date().isoformat()


def main() -> int:
    if not CA.exists():
        raise SystemExit(f"BLOCKED: missing {CA}")

    with CA.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    found = []

    for row in rows:
        symbol = row.get("symbol", "").strip().upper()
        raw_date = row.get("exDate", "").strip()

        if not raw_date:
            continue

        try:
            ex_date = normalize_nse_date(raw_date)
        except ValueError:
            continue

        if (symbol, ex_date) not in TARGETS:
            continue

        match = PATTERN.search(row.get("subject", ""))

        if not match:
            print(
                "BLOCKED: rights subject could not be parsed:",
                row.get("subject"),
            )
            return 1

        found.append(
            {
                "symbol": symbol,
                "ex_date": ex_date,
                "ratio_A": int(match.group("a")),
                "ratio_B": int(match.group("b")),
                "issue_price": float(match.group("p")),
                "subject": row.get("subject", ""),
                "record_date": row.get("recDate", ""),
            }
        )

    if len(found) != len(TARGETS):
        print(
            "BLOCKED: expected three PIT rights events, found",
            len(found),
        )
        for x in found:
            print(x)
        return 1

    print("PHASE 1A P6 — RIGHTS TREATMENT AUDIT")
    print("Reference methodology: NSE corporate-action adjustment guidance")
    print("No production adjustment factor is applied.")
    print()

    for x in sorted(found, key=lambda z: z["ex_date"]):
        print(
            f'{x["ex_date"]} | {x["symbol"]} | '
            f'ratio={x["ratio_A"]}:{x["ratio_B"]} | '
            f'issue_price={x["issue_price"]} | '
            f'record_date={x["record_date"]}'
        )

    print()
    print(
        "STATUS: BLOCKED — cum-date close and explicit "
        "subscription/renunciation policy are required "
        "before production treatment."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
