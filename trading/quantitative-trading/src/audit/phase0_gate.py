"""Deterministic Phase 0 data gate. Fails closed."""
from __future__ import annotations
import csv,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; AUDITS=ROOT/"audits"; REFERENCE=ROOT/"data"/"reference"; RAW=ROOT/"data"/"raw"/"prices"
def read(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def check_official_session_reference():
    p=REFERENCE/"nse_official_sessions.csv"
    if not p.exists():return False,"official NSE session reference missing"
    rows=read(p)
    if not rows:return False,"official NSE session reference empty"
    required={"date","year","is_trading_day","session_type","source","source_reference"}
    if not required<=set(rows[0]):return False,"official session reference schema incomplete"
    dates=[r["date"] for r in rows]
    if len(dates)!=len(set(dates)):return False,"duplicate official session-reference dates"
    if any(r.get("source")!="NSE_OFFICIAL" for r in rows):return False,"session reference contains non-NSE source"
    if any(r.get("session_type")=="MUHURAT" and r.get("is_trading_day","").lower()!="true" for r in rows):return False,"Muhurat session incorrectly marked closed"
    return True,f"{len(rows)} official holiday/session overrides"

def check_calendar():
    p=AUDITS/"nse_trading_calendar_v3.csv"
    if not p.exists():return False,"calendar missing"
    rows=read(p)
    if not rows:return False,"calendar empty"
    dates=[r.get("date","") for r in rows]
    if len(dates)!=len(set(dates)) or any(not x for x in dates):return False,"duplicate/blank calendar dates"
    years={int(r["date"][:4]) for r in rows}
    if years!=set(range(2017,2026)):return False,f"calendar years incomplete: {sorted(years)}"
    if any(r.get("validation_status","").upper()!="VALIDATED" for r in rows):return False,"calendar contains non-validated rows"
    if any("pandas_market_calendars" in r.get("source","").lower() for r in rows):return False,"calendar relies on pandas_market_calendars"
    if any(r.get("source","")!="NSE_OFFICIAL" for r in rows if r.get("is_trading_day","").lower()=="true"):return False,"trading-day rows are not explicitly NSE_OFFICIAL"
    return True,f"{len(rows)} calendar rows present"
def check_membership():
    p=REFERENCE/"nifty50_membership.csv"; b=REFERENCE/"nifty50_baseline.csv"
    if not p.exists() or not b.exists():return False,"PIT ledger or baseline missing"
    rows=read(p)
    if not rows:return False,"PIT ledger empty"
    required={"effective_date","symbol","company_name","isin","action"}
    if not required<=set(rows[0]):return False,"PIT schema incomplete"
    if any(r.get("action") not in {"INCLUSION","EXCLUSION"} or not r.get("isin") or not r.get("symbol") for r in rows):return False,"PIT contains incomplete/invalid identity"
    audit=AUDITS/"pit_membership_reconstruction.csv"
    if not audit.exists():return False,"PIT reconstruction audit not run"
    ar=read(audit)
    if not ar or any(r.get("status")!="PASS" for r in ar):return False,"PIT reconstruction audit has not passed"
    return True,f"{len(rows)} transition rows + passing reconstruction audit"
def check_identity_events():
    p=REFERENCE/"security_identity_events.csv"
    if not p.exists():return False,"security identity event ledger missing"
    rows=read(p)
    required={"event_date","symbol","event_type","old_isin","new_isin","source","source_reference"}
    if not rows or not required<=set(rows[0]):return False,"identity-event schema incomplete"
    keys={(r["symbol"],r["event_type"],r["old_isin"],r["new_isin"]) for r in rows}
    required_events={
        ("YESBANK","SUBDIVISION","INE528G01019","INE528G01027"),
        ("YESBANK","RECONSTRUCTION","INE528G01027","INE528G01035"),
        ("HDFC","AMALGAMATION","INE001A01036","INE040A01034"),
    }
    if not required_events<=keys:return False,"required historical identity events missing"
    if any(r.get("source")!="OFFICIAL" for r in rows):return False,"identity event has non-official source"
    return True,f"{len(rows)} canonical identity events"

def check_manifest():
    p=RAW/"download_manifest.csv"
    if not p.exists():return False,"raw price manifest missing"
    rows=read(p)
    if not rows:return False,"raw manifest empty"
    required={"date","format","url","download_status","http_status","file_size","sha256"}
    if not required<=set(rows[0]):return False,"manifest schema incomplete"
    dates=[r["date"] for r in rows]
    if len(dates)!=len(set(dates)):return False,"manifest contains duplicate dates"
    failed=[r for r in rows if r.get("download_status")!="downloaded" and r.get("download_status")!="already_present"]
    if failed:return False,f"{len(failed)} non-completed manifest rows"
    if any(len(r.get("sha256",""))!=64 or r.get("http_status")!="200" for r in rows):return False,"manifest contains invalid completed rows"
    cal=[r["date"] for r in read(AUDITS/"nse_trading_calendar_v3.csv") if r.get("is_trading_day","").lower()=="true"]
    if set(dates)!=set(cal):return False,f"manifest/calendar mismatch: manifest={len(dates)} calendar={len(cal)}"
    return True,f"{len(rows)} trading-date downloads recorded"
def check_hashes():
    p=RAW/"download_manifest.csv"
    if not p.exists():return False,"cannot hash-check without manifest"
    rows=read(p)
    for r in rows:
        path=RAW/r["format"]/Path(r["url"]).name
        if not path.exists():return False,f"missing raw file: {path}"
        h=hashlib.sha256(path.read_bytes()).hexdigest()
        if h!=r["sha256"]:return False,f"SHA-256 mismatch: {path.name}"
    return True,f"{len(rows)} local files hash-verified"
def main():
    print("="*64+"\nPHASE 0 DATA GATE\n"+"="*64)
    checks=[("Official session ref",check_official_session_reference),("Trading calendar",check_calendar),("PIT membership",check_membership),("Security identity",check_identity_events),("Raw manifest",check_manifest),("Raw file hashes",check_hashes)]
    failures=[]
    for name,fn in checks:
        try:ok,msg=fn()
        except Exception as e:ok,msg=False,f"check crashed: {e}"
        print(f"{name:<24} {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok:failures.append(f"{name}: {msg}")
    print("-"*64)
    if failures:
        print("PHASE 0: FAIL")
        for x in failures:print("- "+x)
        return 1
    print("PHASE 0: PASS")
    return 0
if __name__=="__main__":raise SystemExit(main())
