"""Create the independent NSE TRI verification worksheet.
Rows remain PENDING until the values are independently checked against NSE's
historical Total Returns Index report. The gate will not accept PENDING rows.
"""
from __future__ import annotations
import csv,json
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

def main():
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    checks = [
        ("2019-01-01","15114.90","OFFICIAL_NSE","https://www.nseindia.com/all-reports","NSE All Reports explicitly shows 01-Jan-2019 = 15114.9."),
        ("2020-01-01","","PENDING_OFFICIAL_NSE","https://www.nseindia.com/all-reports","Exact official NSE value still requires direct historical-report verification."),
        ("2021-01-01","","PENDING_OFFICIAL_NSE","https://www.nseindia.com/all-reports","Exact official NSE value still requires direct historical-report verification."),
        ("2022-01-03","","PENDING_OFFICIAL_NSE","https://www.nseindia.com/all-reports","Exact official NSE value still requires direct historical-report verification."),
        ("2023-01-02","","PENDING_OFFICIAL_NSE","https://www.nseindia.com/all-reports","Exact official NSE value still requires direct historical-report verification."),
    ]
    tri=load_tri()
    rows=[]
    for d, external, level, source, note in checks:
        local=tri.get(d,{}).get("value","")
        status="PASS" if level == "OFFICIAL_NSE" and local and abs(float(local)-float(external)) < 1e-6 else "PENDING"
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
