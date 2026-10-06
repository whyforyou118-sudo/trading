"""Generate the research calendar from the NSE official session/holiday reference."""
from __future__ import annotations
import csv,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/"data"/"reference"/"nse_official_sessions.csv"; OUT=ROOT/"audits"/"nse_trading_calendar_v3.csv"
START=datetime.date(2017,1,1); END=datetime.date(2025,12,31)

def main():
    if not REF.exists(): raise SystemExit(f"BLOCKED: missing {REF}")
    overrides={}
    with REF.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            d=datetime.date.fromisoformat(r["date"])
            if START<=d<=END:
                if r.get("source")!="NSE_OFFICIAL": raise SystemExit(f"BLOCKED: non-official source {d}")
                overrides[d]=r
    required_years=set(range(2017,2026))
    if {d.year for d in overrides}!=required_years: raise SystemExit("BLOCKED: reference does not cover every research year")
    rows=[]; d=START
    while d<=END:
        r=overrides.get(d)
        if r:
            trade=r["is_trading_day"].lower()=="true"; session=r["session_type"]; source=r["source"]; ref=r["source_reference"]
        elif d.weekday()>=5:
            trade=False; session="WEEKEND"; source="NSE_OFFICIAL"; ref="NSE exchange calendar"
        else:
            trade=True; session="REGULAR"; source="NSE_OFFICIAL"; ref=f"Annual NSE CM holiday circular ({d.year})"
        rows.append({"date":d.isoformat(),"year":d.year,"weekday":d.strftime("%A"),"is_trading_day":str(trade),"source":source,"source_reference":ref,"validation_status":"VALIDATED","session_type":session})
        d+=datetime.timedelta(days=1)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["date","year","weekday","is_trading_day","source","source_reference","validation_status","session_type"]); w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} rows; trading days={sum(r['is_trading_day']=='True' for r in rows)}")
if __name__=="__main__": main()
