"""Create the independent NSE TRI verification worksheet.
Rows remain PENDING until the values are independently checked against NSE's
historical Total Returns Index report. The gate will not accept PENDING rows.
"""
from __future__ import annotations
import csv,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"
TRI=ROOT/"data/reference/nifty50_tri.csv"
OUT=ROOT/"audits/phase05_tri_verification.csv"
NSE_REF="https://www.nseindia.com/all-reports"

def load_tri():
    if not TRI.exists():
        raise FileNotFoundError(
            f"TRI dataset missing: {TRI}. Run src/data/download_nifty50_tri.py first."
        )
    with TRI.open("r",encoding="utf-8-sig",newline="") as f:
        return {r["date"]:r for r in csv.DictReader(f)}

def fetch_official_value(date_str: str):
    data_path = ROOT / "src" / "data"
    sys.path.insert(0, str(data_path))
    from download_nifty50_tri import make_session, request_chunk
    import datetime
    d = datetime.date.fromisoformat(date_str)
    with make_session() as session:
        rows = request_chunk(session, d, d)
    matches = [r for r in rows if r["date"] == date_str]
    if len(matches) != 1:
        raise RuntimeError(f"official NSE Indices returned {len(matches)} rows for {date_str}")
    return float(matches[0]["value"]), matches[0]["source_reference"]

def main():
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    checks = ["2019-01-01","2020-01-01","2021-01-01","2022-01-03","2023-01-02"]
    tri=load_tri()
    rows=[]
    for d in checks:
        local=tri.get(d,{}).get("value","")
        try:
            external, source = fetch_official_value(d)
            status="PASS" if local and abs(float(local)-external) < 1e-6 else "FAIL"
            note="Fresh official NSE Indices historical TRI lookup matches the local TRI value."
            level="OFFICIAL_NSE_INDICES_LIVE"
        except Exception as exc:
            external=""
            source="https://www.niftyindices.com/reports/historical-data"
            status="PENDING"
            note=f"Official NSE Indices lookup failed: {exc}"
            level="PENDING_OFFICIAL_NSE_INDICES"
        rows.append({
            "check":f"TRI_VALUE_{d}",
            "status":status,
            "evidence":note,
            "date":d,
            "local_value":local,
            "official_value":external,
            "official_source_reference":source,
            "evidence_level":level
        })

    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["check","status","evidence","date","local_value","official_value","official_source_reference","evidence_level"])
        w.writeheader(); w.writerows(rows)
    print("PHASE 0.5 TRI VERIFICATION WORKSHEET")
    print(f"Wrote {len(rows)} verification rows: {OUT}")
    print("Only direct OFFICIAL_NSE evidence can produce PASS. PENDING_OFFICIAL_NSE rows keep the Phase 0.5 official-evidence requirement blocked.")
    return 0

if __name__=="__main__": raise SystemExit(main())
