"""Phase 0.5 transaction-cost feasibility calculator."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"; OUT=ROOT/"audits/phase05_cost_feasibility.csv"

def load_schedule(path):
    if not path.exists(): raise RuntimeError(f"cost schedule missing: {path}")
    with path.open("r",encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    required={"effective_from","effective_to","brokerage_pct","brokerage_fixed","stt_buy_pct","stt_sell_pct","transaction_charge_pct","sebi_per_crore","stamp_buy_pct","gst_pct","dp_per_scrip","verified","source_reference"}
    if not rows or not required<=set(rows[0]): raise RuntimeError("cost schedule schema incomplete")
    if any(r["verified"].strip().upper()!="TRUE" for r in rows): raise RuntimeError("cost schedule contains unverified rows")
    if any(not r["source_reference"].strip() for r in rows): raise RuntimeError("every cost row needs a source reference")
    return rows

def pct(row,key): return float(row[key])/100.0

def scenario(row,capital,holdings=5,rebalances=4,slippage=0.001):
    trade_value=capital
    annual_turnover=trade_value*2*rebalances
    buy=trade_value*rebalances; sell=buy
    trades=holdings*2*rebalances
    brokerage=annual_turnover*pct(row,"brokerage_pct")+trades*float(row["brokerage_fixed"])
    stt=buy*pct(row,"stt_buy_pct")+sell*pct(row,"stt_sell_pct")
    transaction=annual_turnover*pct(row,"transaction_charge_pct")
    sebi=annual_turnover/1e7*float(row["sebi_per_crore"])
    stamp=buy*pct(row,"stamp_buy_pct")
    gst=(brokerage+transaction+sebi)*pct(row,"gst_pct")
    dp=holdings*rebalances*float(row["dp_per_scrip"])
    slip=annual_turnover*slippage
    total=brokerage+stt+transaction+sebi+stamp+gst+dp+slip
    return {"capital":capital,"annual_turnover":annual_turnover,"brokerage":brokerage,"stt":stt,"transaction_charges":transaction,"sebi":sebi,"stamp_duty":stamp,"gst":gst,"dp_charges":dp,"slippage":slip,"total_cost":total,"cost_pct_of_starting_capital":total/capital,"slippage_assumption":slippage,"scenario":"100_percent_liquidate_and_rebuild_each_quarter"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--slippage",type=float,default=0.001); a=ap.parse_args()
    cfg=json.loads(CFG.read_text(encoding="utf-8")); schedule=load_schedule(ROOT/cfg["cost_schedule_file"])
    if not cfg.get("cost_schedule_verified",False): raise SystemExit("BLOCKED: config cost_schedule_verified=false. Verify the schedule and source/effective-date review before enabling.")
    rows=[]
    for cap in cfg["capital_scenarios"]:
        for s in schedule:
            x=scenario(s,float(cap),slippage=a.slippage)
            x.update(effective_from=s["effective_from"],effective_to=s["effective_to"],source_reference=s["source_reference"]); rows.append(x)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("PHASE 0.5 COST FEASIBILITY")
    for cap in cfg["capital_scenarios"]:
        m=[r for r in rows if r["capital"]==cap]; worst=max(m,key=lambda r:r["cost_pct_of_starting_capital"])
        print(f"₹{cap:,.0f}: worst modeled drag = {worst['cost_pct_of_starting_capital']:.2%}")
    print(f"Artifact: {OUT}"); return 0
if __name__=="__main__": raise SystemExit(main())
