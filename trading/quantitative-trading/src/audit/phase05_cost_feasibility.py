"""Phase 0.5 transaction-cost feasibility calculator."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"; OUT=ROOT/"audits/phase05_cost_feasibility.csv"

SCHEDULE_FIELDS={
    "effective_from","effective_to","brokerage_pct","brokerage_fixed",
    "stt_buy_pct","stt_sell_pct","transaction_charge_pct","sebi_per_crore",
    "stamp_buy_pct","gst_pct","dp_per_scrip","verified","source_reference",
    "stamp_basis"
}
OUTPUT_FIELDS=[
    "status","reason","capital","annual_turnover","brokerage","stt",
    "transaction_charges","sebi","stamp_duty","gst","dp_charges","slippage",
    "total_cost","cost_pct_of_starting_capital","slippage_assumption",
    "scenario","stamp_basis","effective_from","effective_to","source_reference"
]

def blocked(reason, slippage):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=OUTPUT_FIELDS)
        w.writeheader()
        w.writerow({
            "status":"BLOCKED",
            "reason":reason,
            "slippage_assumption":slippage,
        })
    print("PHASE 0.5 COST FEASIBILITY")
    print(f"STATUS: BLOCKED — {reason}")
    print(f"Artifact: {OUT}")
    return 1

def load_schedule(path):
    if not path.exists():
        return None,f"cost schedule missing: {path.relative_to(ROOT)}"
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if not rows:
        return None,f"cost schedule is empty: {path.relative_to(ROOT)}"
    if not SCHEDULE_FIELDS<=set(rows[0]):
        missing=", ".join(sorted(SCHEDULE_FIELDS-set(rows[0])))
        return None,f"cost schedule schema incomplete; missing fields: {missing}"
    if any(r["verified"].strip().upper()!="TRUE" for r in rows):
        return None,"cost schedule contains unverified rows"
    if any(not r["source_reference"].strip() for r in rows):
        return None,"every cost row needs a source reference"
    return rows,None

def pct(row,key): return float(row[key])/100.0

def scenario(row,capital,holdings=5,rebalances=4,slippage=0.001,stamp_pct_override=None,scenario_label=None):
    trade_value=capital
    annual_turnover=trade_value*2*rebalances
    buy=trade_value*rebalances; sell=buy
    trades=holdings*2*rebalances
    brokerage=annual_turnover*pct(row,"brokerage_pct")+trades*float(row["brokerage_fixed"])
    stt=buy*pct(row,"stt_buy_pct")+sell*pct(row,"stt_sell_pct")
    transaction=annual_turnover*pct(row,"transaction_charge_pct")
    sebi=annual_turnover/1e7*float(row["sebi_per_crore"])
    stamp_rate=pct(row,"stamp_buy_pct") if stamp_pct_override is None else float(stamp_pct_override)
    stamp=buy*stamp_rate
    gst=(brokerage+transaction+sebi)*pct(row,"gst_pct")
    dp=holdings*rebalances*float(row["dp_per_scrip"])
    slip=annual_turnover*slippage
    total=brokerage+stt+transaction+sebi+stamp+gst+dp+slip
    return {
        "capital":capital,"annual_turnover":annual_turnover,"brokerage":brokerage,
        "stt":stt,"transaction_charges":transaction,"sebi":sebi,
        "stamp_duty":stamp,"gst":gst,"dp_charges":dp,"slippage":slip,
        "total_cost":total,"cost_pct_of_starting_capital":total/capital,
        "slippage_assumption":slippage,
        "scenario":scenario_label or "100_percent_liquidate_and_rebuild_each_quarter",
        "stamp_basis":row.get("stamp_basis","")
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--slippage",type=float,default=0.001)
    a=ap.parse_args()
    cfg=json.loads(CFG.read_text(encoding="utf-8"))

    schedule,error=load_schedule(ROOT/cfg["cost_schedule_file"])
    if error:
        return blocked(error,a.slippage)
    if not cfg.get("cost_schedule_verified",False):
        return blocked(
            "config cost_schedule_verified=false; verify the schedule and source/effective-date review before enabling",
            a.slippage,
        )

    rows=[]
    for cap in cfg["capital_scenarios"]:
        for s in schedule:
            basis=s.get("stamp_basis","")
            if basis == "STATE_AGNOSTIC_SENSITIVITY_ANCHOR":
                anchor=pct(s,"stamp_buy_pct")
                labels=[("STATE_AGNOSTIC_STAMP_SENSITIVITY_ANCHOR", anchor)]
            else:
                labels=[("100_percent_liquidate_and_rebuild_each_quarter", None)]
            for label,override in labels:
                x=scenario(
                    s,float(cap),slippage=a.slippage,
                    stamp_pct_override=override,
                    scenario_label=label
                )
                x.update(
                    status="PASS",
                    reason="verified schedule row; stamp-duty basis explicitly labeled",
                    effective_from=s["effective_from"],
                    effective_to=s["effective_to"],
                    source_reference=s["source_reference"],
                )
                rows.append(x)

    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=OUTPUT_FIELDS)
        w.writeheader()
        w.writerows(rows)

    print("PHASE 0.5 COST FEASIBILITY")
    for cap in cfg["capital_scenarios"]:
        m=[r for r in rows if r["capital"]==cap]
        worst=max(m,key=lambda r:r["cost_pct_of_starting_capital"])
        print(f"₹{cap:,.0f}: worst modeled drag = {worst['cost_pct_of_starting_capital']:.2%}")
    print(f"Artifact: {OUT}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
