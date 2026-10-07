"""Fail-closed Phase 0.5 evidence gate."""
from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; CFG=ROOT/"config/phase05_config.json"
def read(p):
    with p.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def artifact(p,required,min_rows=1):
    if not p.exists(): return False,f"missing: {p.relative_to(ROOT)}"
    rows=read(p)
    if len(rows)<min_rows:return False,f"empty/insufficient: {p.relative_to(ROOT)}"
    if not required<=set(rows[0]):return False,f"schema incomplete: {p.relative_to(ROOT)}"
    return True,f"{len(rows)} rows"
def main():
    cfg=json.loads(CFG.read_text(encoding="utf-8")); checks=[]
    checks.append(("Statistical feasibility",artifact(ROOT/"audits/phase05_statistical_feasibility.csv",{"quarterly_decision_count","approx_mdes_sharpe","volatility_scaled_annualized_excess_return_mde"})))
    checks.append(("Capital feasibility",artifact(ROOT/"audits/phase05_capital_feasibility.csv",{"capital","rebalance_date","unbuyable_count","cash_pct","mean_abs_weight_deviation"})))
    checks.append(("Cost feasibility",artifact(ROOT/"audits/phase05_cost_feasibility.csv",{"capital","total_cost","cost_pct_of_starting_capital","slippage_assumption"})))
    checks.append(("TRI source/data",artifact(ROOT/cfg["tri_file"],{"date","value","source","source_reference"},100)))
    checks.append(("TRI verification",artifact(ROOT/cfg["tri_verification_file"],{"check","status","evidence"})))
    checks.append(("PIT external reconciliation",artifact(ROOT/cfg["pit_external_file"],{"effective_date","check","status","official_source_reference"},int(cfg["pit_external_dates_required"]))))
    checks.append(("Corporate-action sample",artifact(ROOT/cfg["corporate_action_file"],{"event_id","event_type","security","status","source_reference"},int(cfg["corporate_action_sample_required"]))))
    if not cfg.get("cost_schedule_verified",False): checks.append(("Zerodha cost schedule",(False,"config flag cost_schedule_verified=false")))
    print("="*68); print("PHASE 0.5 RESEARCH FEASIBILITY GATE"); print("="*68); failed=[]
    for name,(ok,msg) in checks:
        print(f"{name:<30} {'PASS' if ok else 'FAIL'} — {msg}")
        if not ok: failed.append(f"{name}: {msg}")
    print("-"*68)
    if failed:
        print("PHASE 0.5: BLOCKED"); print("No Phase 1A strategy/performance backtest is authorized."); return 1
    print("PHASE 0.5: EVIDENCE COMPLETE"); print("This is an evidence-completeness result, not an alpha verdict."); return 0
if __name__=="__main__": raise SystemExit(main())
