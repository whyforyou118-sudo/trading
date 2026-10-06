"""Regression checks for the NSE research calendar."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "audits" / "nse_trading_calendar_v3.csv"

EXPECTED = {
    "2017-01-26": False, "2017-10-19": True,
    "2018-01-26": False, "2018-11-07": True,
    "2019-10-27": True, "2020-11-14": True,
    "2021-11-04": True, "2022-10-24": True,
    "2023-11-12": True, "2023-11-14": False,
    "2024-11-01": True, "2025-08-15": False,
}

with CAL.open(encoding="utf-8-sig", newline="") as f:
    rows = {r["date"]: r for r in csv.DictReader(f)}

assert len(rows) == 3287, len(rows)
assert {int(d[:4]) for d in rows} == set(range(2017, 2026))

for date, expected in EXPECTED.items():
    assert date in rows, f"missing {date}"
    actual = rows[date]["is_trading_day"].lower() == "true"
    assert actual == expected, f"{date}: expected {expected}, got {actual}"

for date, row in rows.items():
    if row["session_type"] == "MUHURAT":
        assert row["is_trading_day"].lower() == "true", date

print("NSE calendar regression: PASS")
