"""Deterministic Phase 0 gate. Fails closed until critical checks pass."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
AUDITS = ROOT / "audits"
REFERENCE = ROOT / "data" / "reference"

def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def check_calendar():
    path = AUDITS / "nse_trading_calendar_v3.csv"
    if not path.exists(): return False, "calendar file missing"
    rows = read_csv(path)
    if not rows: return False, "calendar is empty"
    dates = [r.get("date", "") for r in rows]
    if len(dates) != len(set(dates)): return False, "duplicate calendar dates"
    statuses = {r.get("validation_status", "").upper() for r in rows}
    sources = {r.get("source", "").lower() for r in rows}
    if "UNVERIFIED" in statuses: return False, "calendar contains UNVERIFIED rows"
    if any("pandas_market_calendars" in s for s in sources): return False, "calendar relies on pandas_market_calendars"
    aug15 = next((r for r in rows if r.get("date") == "2025-08-15"), None)
    if aug15 and str(aug15.get("is_trading_day", "")).lower() == "true": return False, "2025-08-15 marked as trading day"
    return True, f"{len(rows)} calendar rows present"

def check_membership():
    path = REFERENCE / "nifty50_membership.csv"
    if not path.exists(): return False, "PIT membership file missing"
    rows = read_csv(path)
    if not rows: return False, "PIT membership file is empty"
    required = {"effective_date", "symbol", "isin", "action"}
    missing = required - set(rows[0])
    if missing: return False, f"membership columns missing: {sorted(missing)}"
    return True, f"{len(rows)} membership transition rows present"

def main():
    print("=" * 60)
    print("PHASE 0 DATA GATE")
    print("=" * 60)
    failures = []
    for name, check in [("Trading calendar", check_calendar), ("PIT membership", check_membership)]:
        ok, detail = check()
        print(f"{name:<24} {"PASS" if ok else "FAIL"} — {detail}")
        if not ok: failures.append(f"{name}: {detail}")
    print("-" * 60)
    if failures:
        print("PHASE 0: FAIL")
        for failure in failures: print(f"- {failure}")
        return 1
    print("PHASE 0: PARTIAL — integrity, identity, corporate-action, and PIT-price checks remain.")
    return 2

if __name__ == "__main__": raise SystemExit(main())