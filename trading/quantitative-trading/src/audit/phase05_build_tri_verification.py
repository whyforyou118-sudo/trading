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
    with TRI.open("r",encoding="utf-8-sig",newline="") as f:
        return {r["date"]:r for r in csv.DictReader(f)}

def main():
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    dates=["2019-01-01","2020-01-01","2021-01-01","2022-01-03","2023-01-02"]
    tri=load_tri()
    rows=[]
    for d in dates:
        rows.append({
            "check":f"NSE_TRI_VALUE_{d}",
            "status":"PENDING",
            "evidence":f"Local TRI value={tri.get(d,{}).get('value','MISSING')}; independently compare with NSE historical Total Returns Index report",
            "date":d,
            "local_value":tri.get(d,{}).get("value",""),
            "official_value":"",
            "official_source_reference":NSE_REF
        })
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["check","status","evidence","date","local_value","official_value","official_source_reference"])
        w.writeheader(); w.writerows(rows)
    print("PHASE 0.5 TRI VERIFICATION WORKSHEET")
    print(f"Wrote {len(rows)} PENDING verification rows: {OUT}")
    print("Do not mark PASS until each local value is independently checked against NSE.")
    return 0

if __name__=="__main__": raise SystemExit(main())
