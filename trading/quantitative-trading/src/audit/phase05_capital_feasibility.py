"""Phase 0.5 whole-share capital-feasibility audit.

Input columns: rebalance_date,rank,symbol,execution_price.
No P&L is calculated.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"; OUT=ROOT/"audits/phase05_capital_feasibility.csv"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input"); a=ap.parse_args()
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    path=ROOT/(a.input or cfg["capital_feasibility_selection_file"])
    if not path.exists(): raise SystemExit(f"BLOCKED: selection artifact missing: {path}\nExpected columns: rebalance_date,rank,symbol,execution_price.")
    with path.open("r",encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    required={"rebalance_date","rank","symbol","execution_price"}
    if not rows or not required<=set(rows[0]): raise SystemExit("BLOCKED: selection artifact schema incomplete")
    for r in rows: r["rank"]=int(r["rank"]); r["execution_price"]=float(r["execution_price"])
    rows=[r for r in rows if r["rank"]<=int(cfg["primary_holdings"])]
    grouped={}
    for r in rows: grouped.setdefault(r["rebalance_date"],[]).append(r)
    out=[]
    for capital in cfg["capital_scenarios"]:
        for d,selected in sorted(grouped.items()):
            if len(selected)!=int(cfg["primary_holdings"]):
                out.append({"capital":capital,"rebalance_date":d,"selected_count":len(selected),"unbuyable_count":"","cash_after_allocation":"","cash_pct":"","mean_abs_weight_deviation":"","max_abs_weight_deviation":"","status":"INVALID_SELECTION_COUNT"}); continue
            target=capital/int(cfg["primary_holdings"]); spent=0.0; dev=[]; unbuyable=0
            for r in selected:
                p=r["execution_price"]; q=int(target//p) if p>0 else 0
                if q==0: unbuyable+=1
                actual=q*p; spent+=actual; dev.append(abs(actual/capital-1/int(cfg["primary_holdings"])))
            cash=capital-spent
            out.append({"capital":capital,"rebalance_date":d,"selected_count":len(selected),"unbuyable_count":unbuyable,"cash_after_allocation":round(cash,6),"cash_pct":cash/capital,"mean_abs_weight_deviation":sum(dev)/len(dev),"max_abs_weight_deviation":max(dev),"status":"PASS"})
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
    print("PHASE 0.5 CAPITAL FEASIBILITY")
    for cap in cfg["capital_scenarios"]:
        x=[r for r in out if r["capital"]==cap and r["status"]=="PASS"]
        if x:
            print(f"₹{cap:,.0f}: unbuyable rebalances={sum(int(r['unbuyable_count'])>0 for r in x)}/{len(x)}, mean cash={sum(float(r['cash_pct']) for r in x)/len(x):.2%}, mean abs weight deviation={sum(float(r['mean_abs_weight_deviation']) for r in x)/len(x):.2%}")
        else: print(f"₹{cap:,.0f}: no valid rebalance rows")
    print(f"Artifact: {OUT}"); return 0
if __name__=="__main__": raise SystemExit(main())
