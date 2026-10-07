"""Phase 0.5 deterministic retail-friction report.

Reads the existing Top-5 feasibility artifact and reports whole-share/cash
constraints. It does not simulate strategy performance.
"""
from __future__ import annotations
import csv
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "audits" / "phase05_top5_feasibility.csv"
OUTPUT = ROOT / "audits" / "phase05_retail_friction_report.csv"

CAPITALS = [20000,25000,50000,100000,500000,1000000]
CONSERVATIVE_COST_DRAG = {
    20000: 0.0329,
    25000: 0.0297,
    50000: 0.0233,
    100000: 0.0201,
    500000: 0.0176,
    1000000: 0.0173,
}

def f(row, *names):
    for n in names:
        if n in row and row[n] not in ("", None):
            return float(row[n])
    return None

def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing required artifact: {INPUT}")

    rows = list(csv.DictReader(INPUT.open(encoding="utf-8-sig")))
    if not rows:
        raise SystemExit("Top-5 feasibility artifact is empty")

    print("PHASE 0.5 RETAIL FRICTION REPORT")
    print(f"Input: {INPUT}")
    print(f"Rows: {len(rows)}")

    # The existing feasibility artifact is expected to contain one row per
    # selected stock per executable rebalance. Aggregate by capital/date.
    date_key = "rebalance_date"
    cap_key = "capital"
    grouped = {}
    for r in rows:
        if date_key not in r or cap_key not in r:
            raise SystemExit(f"Unexpected feasibility schema; required {date_key}/{cap_key}")
        key=(r[cap_key],r[date_key])
        grouped.setdefault(key,[]).append(r)

    out=[]
    for cap in CAPITALS:
        dates=sorted({d for c,d in grouped if int(float(c))==cap})
        metrics=[]
        for d in dates:
            rr=grouped[(str(cap),d)] if (str(cap),d) in grouped else grouped.get((str(cap),d),[])
            if not rr:
                # tolerate numeric formatting in the CSV
                rr=[v for (c,dd),v in grouped.items() if int(float(c))==cap and dd==d][0]
            cash_vals=[f(x,"cash_pct","cash_weight","cash_fraction") for x in rr]
            dev_vals=[f(x,"abs_weight_deviation","weight_deviation") for x in rr]
            unbuyable_vals=[x.get("unbuyable","").strip().lower() in {"1","true","yes","y"} for x in rr]
            cash=max([x for x in cash_vals if x is not None], default=None)
            dev=max([x for x in dev_vals if x is not None], default=None)
            metrics.append((cash,dev,any(unbuyable_vals),sum(unbuyable_vals)))
        valid_cash=[x[0] for x in metrics if x[0] is not None]
        valid_dev=[x[1] for x in metrics if x[1] is not None]
        n=len(metrics)
        unbuy=sum(x[2] for x in metrics)
        avg_cash=mean(valid_cash) if valid_cash else float("nan")
        med_cash=median(valid_cash) if valid_cash else float("nan")
        max_cash=max(valid_cash) if valid_cash else float("nan")
        avg_dev=mean(valid_dev) if valid_dev else float("nan")
        cost=CONSERVATIVE_COST_DRAG[cap]
        # Conservative break-even gross return if costs are modeled as a
        # percentage of starting capital: gross return must cover that drag.
        break_even=cost
        out.append({
            "capital":cap,
            "executable_rebalances":n,
            "unbuyable_rebalances":unbuy,
            "unbuyable_fraction":unbuy/n if n else "",
            "mean_cash":avg_cash,
            "median_cash":med_cash,
            "max_cash":max_cash,
            "mean_abs_weight_deviation":avg_dev,
            "conservative_cost_drag":cost,
            "conservative_break_even_gross_return":break_even,
            "interpretation":"feasibility diagnostic; not strategy performance"
        })
        print(
            f"₹{cap:,}: rebalances={n}, unbuyable={unbuy}/{n}, "
            f"mean_cash={avg_cash:.2%}, median_cash={med_cash:.2%}, "
            f"max_cash={max_cash:.2%}, mean_abs_dev={avg_dev:.2%}, "
            f"conservative_cost_drag={cost:.2%}"
        )

    with OUTPUT.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=out[0].keys())
        w.writeheader(); w.writerows(out)
    print(f"Wrote: {OUTPUT}")
    print("PASS: deterministic feasibility report generated; no performance return was calculated.")

if __name__=="__main__":
    main()
