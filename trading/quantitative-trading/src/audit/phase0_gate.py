"""Deterministic Phase 0 gate. Fails closed until critical checks pass."""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDITS = ROOT / "audits"
REFERENCE = ROOT / "data" / "reference"
RAW = ROOT / "data" / "raw"

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
    if any(not r.get("date") for r in rows): return False, "calendar contains blank dates"
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
    required = {"effective_date", "symbol", "company_name", "isin", "action"}
    missing = required - set(rows[0])
    if missing: return False, f"membership columns missing: {sorted(missing)}"
    if any(r.get("action") not in {"INCLUSION", "EXCLUSION"} for r in rows):
        return False, "unknown membership action"
    keys = [(r.get("effective_date"), r.get("symbol"), r.get("action")) for r in rows]
    if len(keys) != len(set(keys)): return False, "duplicate membership transition rows"
    if any(not r.get("symbol") or not r.get("isin") or not r.get("company_name") for r in rows):
        return False, "membership row has incomplete identity"
    baseline = REFERENCE / "nifty50_baseline.csv"
    if not baseline.exists(): return False, "authoritative NIFTY 50 baseline snapshot missing"
    return True, f"{len(rows)} transition rows + baseline present"

def check_raw_manifest():
    manifest = RAW / "prices" / "download_manifest.csv"
    if not manifest.exists(): return False, "raw price manifest missing (expected locally)"
    rows = read_csv(manifest)
    if not rows: return False, "raw price manifest is empty"
    required = {"date", "format", "url", "download_status", "http_status", "file_size", "sha256"}
    missing = required - set(rows[0])
    if missing: return False, f"manifest columns missing: {sorted(missing)}"
    completed = [r for r in rows if r.get("download_status") in {"downloaded", "already_present"}]
    failed = [r for r in rows if r.get("download_status") == "failed"]
    if failed: return False, f"{len(failed)} terminal download failures"
    if not completed: return False, "no completed downloads"
    for r in completed:
        if len(r.get("sha256", "")) != 64: return False, f"invalid SHA-256: {r.get('date')}"
        if r.get("http_status") != "200": return False, f"completed download without HTTP 200: {r.get('date')}"
    return True, f"{len(completed)} completed manifest rows"

def check_local_hashes():
    manifest = RAW / "prices" / "download_manifest.csv"
    if not manifest.exists(): return False, "cannot hash-check without manifest"
    rows = read_csv(manifest)
    checked = 0
    for row in rows:
        if row.get("download_status") not in {"downloaded", "already_present"}: continue
        filename = Path(row.get("url", "")).name
        path = RAW / "prices" / row.get("format", "") / filename
        if not path.exists(): return False, f"manifest file missing locally: {path}"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checked += 1
        if digest != row.get("sha256"): return False, f"SHA-256 mismatch: {path}"
    return True, f"{checked} local files hash-verified"

def main():
    print("=" * 64)
    print("PHASE 0 DATA GATE")
    print("=" * 64)
    checks = [
        ("Trading calendar", check_calendar),
        ("PIT membership", check_membership),
        ("Raw manifest", check_raw_manifest),
        ("Raw file hashes", check_local_hashes),
    ]
    failures = []
    for name, check in checks:
        try:
            ok, detail = check()
        except Exception as exc:
            ok, detail = False, f"check crashed: {exc}"
        print(f"{name:<24} {'PASS' if ok else 'FAIL'} — {detail}")
        if not ok: failures.append(f"{name}: {detail}")
    print("-" * 64)
    if failures:
        print("PHASE 0: FAIL")
        for failure in failures: print(f"- {failure}")
        return 1
    print("PHASE 0: PARTIAL — run validate_pit_membership.py and complete identity,")
    print("corporate-action, PIT-price, and source-reconciliation checks.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
