"""Fail-closed Phase 0.5 evidence gate."""
from __future__ import annotations
import csv,json
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"

def read(p):
    with p.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def artifact(p,required,min_rows=1):
    if not p.exists(): return False,f"missing: {p.relative_to(ROOT)}"
    rows=read(p)
    if len(rows)<min_rows:return False,f"empty/insufficient: {p.relative_to(ROOT)}"
    if not required<=set(rows[0]):return False,f"schema incomplete: {p.relative_to(ROOT)}"
    return True,f"{len(rows)} rows"

def status_artifact(p,required,min_rows=1):
    ok,msg=artifact(p,required,min_rows)
    if not ok:return ok,msg
    rows=read(p)
    bad=[r for r in rows if r.get("status","").upper()!="PASS"]
    if bad:return False,f"{len(bad)} rows are not PASS in {p.relative_to(ROOT)}"
    return True,msg

def check_tri(cfg):
    p=ROOT/cfg["tri_file"]; ok,msg=artifact(p,{"date","value","source","source_reference"},100)
    if not ok:return ok,msg
    rows=read(p); dates=[]
    try:
        for r in rows:
            d=date.fromisoformat(r["date"]); float(r["value"]); dates.append(d)
    except Exception as e:return False,f"invalid TRI row: {e}"
    if len(dates)!=len(set(dates)):return False,"TRI contains duplicate dates"
    start=date.fromisoformat(cfg["research_start"]); end=date.fromisoformat(cfg["research_end"])
    if min(dates)>start or max(dates)<end:return False,"TRI does not cover the full declared research interval"
    if any(not r["source_reference"].strip() for r in rows):return False,"TRI row missing source reference"
    return True,f"{len(rows)} dated observations covering declared interval"

def check_cost_schedule(cfg):
    p=ROOT/cfg["cost_schedule_file"]
    ok,msg=artifact(p,{"effective_from","effective_to","brokerage_pct","brokerage_fixed","stt_buy_pct","stt_sell_pct","transaction_charge_pct","sebi_per_crore","stamp_buy_pct","gst_pct","dp_per_scrip","verified","source_reference"})
    if not ok:return ok,msg
    rows=read(p)
    if any(r["verified"].strip().upper()!="TRUE" for r in rows):return False,"cost schedule contains unverified rows"
    if any(not r["source_reference"].strip() for r in rows):return False,"cost schedule contains missing source references"
    start=date.fromisoformat(cfg["research_start"]); end=date.fromisoformat(cfg["research_end"])
    intervals=[]
    for r in rows:
        a=date.fromisoformat(r["effective_from"]); b=date.fromisoformat(r["effective_to"]) if r["effective_to"].strip() else end
        intervals.append((a,b))
    covered=start
    for a,b in sorted(intervals):
        if a<=covered<=b and b>=covered:
            covered=b
            if covered>=end:return True,f"{len(rows)} verified date-effective cost rows covering research interval"
    return False,"verified cost schedule does not continuously cover the declared research interval"

def main():
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    checks=[]
    checks.append(("Statistical feasibility",artifact(ROOT/"audits/phase05_statistical_feasibility.csv",{"quarterly_decision_count","approx_mdes_sharpe","volatility_scaled_annualized_excess_return_mde"})))
    checks.append(("Top-5 feasibility input",artifact(ROOT/cfg["capital_feasibility_selection_file"],{"rebalance_date","execution_date","rank","symbol","execution_price","price_basis"},1)))
    checks.append(("Capital feasibility",status_artifact(ROOT/"audits/phase05_capital_feasibility.csv",{"capital","rebalance_date","unbuyable_count","cash_pct","mean_abs_weight_deviation"})))
    checks.append(("Cost feasibility",artifact(ROOT/"audits/phase05_cost_feasibility.csv",{"capital","total_cost","cost_pct_of_starting_capital","slippage_assumption"})))
    checks.append(("Zerodha cost schedule",check_cost_schedule(cfg)))
    checks.append(("TRI source/data",check_tri(cfg)))
    checks.append(("TRI verification",status_artifact(ROOT/cfg["tri_verification_file"],{"check","status","evidence"})))
    checks.append(("PIT external reconciliation",status_artifact(ROOT/cfg["pit_external_file"],{"effective_date","check","status","official_source_reference"},int(cfg["pit_external_dates_required"]))))
    checks.append(("Corporate-action sample",status_artifact(ROOT/cfg["corporate_action_file"],{"event_id","event_type","security","status","source_reference"},int(cfg["corporate_action_sample_required"]))))
    print("="*68); print("PHASE 0.5 RESEARCH FEASIBILITY GATE"); print("="*68); failed=[]
    for name,(ok,msg) in checks:
        print(f"{name:<30} {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok: failed.append(f"{name}: {msg}")
    print("-"*68)
    if failed:
        print("PHASE 0.5: BLOCKED")
        print("No Phase 1A strategy/performance backtest is authorized.")
        return 1
    print("PHASE 0.5: EVIDENCE COMPLETE")
    print("This is an evidence-completeness result, not an alpha verdict.")
    return 0

if __name__=="__main__": raise SystemExit(main())
