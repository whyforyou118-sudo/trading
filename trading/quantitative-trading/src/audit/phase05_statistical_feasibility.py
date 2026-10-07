"""Phase 0.5 statistical feasibility diagnostic."""
from __future__ import annotations
import argparse, csv, json
from datetime import date
from pathlib import Path
from statistics import NormalDist

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"
CAL=ROOT/"audits/nse_trading_calendar_v3.csv"
OUT=ROOT/"audits/phase05_statistical_feasibility.csv"

def qdates(start,end):
    rows=[]
    with CAL.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("is_trading_day","").lower()!="true": continue
            d=date.fromisoformat(r["date"])
            if start<=d<=end and d.month in (3,6,9,12): rows.append(d)
    by_q={}
    for d in rows: by_q[(d.year,d.month)]=max(d,by_q.get((d.year,d.month),d))
    return sorted(by_q.values())

def mdes_sharpe(n,alpha,power):
    if n<=1: raise ValueError("n must exceed 1")
    z=NormalDist().inv_cdf(1-alpha)+NormalDist().inv_cdf(power)
    lo,hi=0.0,10.0
    for _ in range(200):
        mid=(lo+hi)/2
        stat=mid/((1+0.5*mid*mid)/n)**0.5
        if stat<z: lo=mid
        else: hi=mid
    return (lo+hi)/2

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--annual-vol",type=float,default=None)
    a=ap.parse_args()
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    start=date.fromisoformat(cfg["research_start"]); end=date.fromisoformat(cfg["research_end"])
    calendar_quarter_ends=qdates(start,end)
    # A quarter-end is not automatically a strategy decision date. The frozen
    # 12M formation + 1M skip design needs one additional month of history.
    # The Top-5 feasibility builder therefore starts only when the required
    # formation endpoint exists inside the available calendar. Keep both
    # counts visible so the diagnostic cannot overstate statistical sample size.
    eligible_dates=[d for d in calendar_quarter_ends if (d.year > start.year or d.month > start.month)]
    n=len(eligible_dates)
    vol=a.annual_vol if a.annual_vol is not None else float(cfg["annual_volatility_diagnostic"])
    sr=mdes_sharpe(n,float(cfg["alpha"]),float(cfg["power"]))
    mde=sr*vol
    result={
        "config_version":cfg["version"],"research_start":start.isoformat(),
        "research_end":end.isoformat(),"calendar_quarter_end_count":len(calendar_quarter_ends),"eligible_strategy_decision_count":n,
        "alpha":cfg["alpha"],"power":cfg["power"],
        "diagnostic_annual_volatility":vol,"approx_mdes_sharpe":sr,
        "volatility_scaled_annualized_excess_return_mde":mde,
        "interpretation":"Design-capability diagnostic only; it does not establish alpha and does not fully account for serial dependence, benchmark correlation, overlapping holding periods or multiple testing.",
        "calendar_quarter_end_dates":";".join(d.isoformat() for d in calendar_quarter_ends),"eligible_strategy_decision_dates":";".join(d.isoformat() for d in eligible_dates)
    }
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=result.keys()); w.writeheader(); w.writerow(result)
    print("PHASE 0.5 STATISTICAL FEASIBILITY")
    print(f"Calendar quarter-ends: {len(calendar_quarter_ends)}")
    print(f"Eligible strategy decision dates: {n}")
    print(f"Approximate MDES Sharpe: {sr:.4f}")
    print(f"Volatility-scaled annualized excess-return MDE: {mde:.2%}")
    print(f"Artifact: {OUT}")
    return 0
if __name__=="__main__": raise SystemExit(main())
