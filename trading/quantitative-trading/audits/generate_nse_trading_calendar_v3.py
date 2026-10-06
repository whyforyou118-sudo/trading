"""Generate the research trading calendar from an NSE-verified session reference.

This script intentionally refuses to infer historical NSE holidays from
pandas_market_calendars, weekends, or manually embedded dates. Populate
data/reference/nse_session_reference.csv from official NSE Capital Market
holiday/session circulars first.
"""
from __future__ import annotations
import csv,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"data"/"reference"/"nse_session_reference.csv"
OUT=ROOT/"audits"/"nse_trading_calendar_v3.csv"
START=datetime.date(2017,1,1); END=datetime.date(2025,12,31)

def main():
    if not REFERENCE.exists():
        raise SystemExit(f"BLOCKED: missing official NSE session reference: {REFERENCE}")
    ref={}
    with REFERENCE.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            d=datetime.date.fromisoformat(r["date"])
            if not START<=d<=END:continue
            if r.get("source","").upper()!="NSE_OFFICIAL":raise SystemExit(f"BLOCKED: non-official source for {d}")
            ref[d]=r
    missing_years=set(range(2017,2026))-{d.year for d in ref}
    if missing_years:raise SystemExit(f"BLOCKED: official session reference missing years: {sorted(missing_years)}")
    rows=[]; d=START
    while d<=END:
        r=ref.get(d)
        if r:
            trade=r["is_trading_day"].strip().lower()=="true"; source="NSE_OFFICIAL"; note=r.get("reason","")
        else:
            trade=d.weekday()<5; source="WEEKDAY_BASELINE"; note="ordinary weekday"
        rows.append({"date":d.isoformat(),"year":d.year,"weekday":d.strftime("%A"),"is_trading_day":str(trade),"source":source,"source_reference":r.get("source_reference","") if r else "weekend rule","validation_status":"VALIDATED" if source=="NSE_OFFICIAL" or d.weekday()>=5 else "UNVERIFIED","reason":note})
        d+=datetime.timedelta(days=1)
    # Every non-weekend session/closure override must be explicitly supported by NSE.
    if any(x["source"]=="WEEKDAY_BASELINE" and x["is_trading_day"]=="True" for x in rows):
        raise SystemExit("BLOCKED: ordinary weekdays are not accepted as validated NSE sessions; reference every trading day explicitly.")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["date","year","weekday","is_trading_day","source","source_reference","validation_status","reason"]);w.writeheader();w.writerows(rows)
    print(f"Wrote {len(rows)} calendar rows to {OUT}")
if __name__=="__main__":main()
