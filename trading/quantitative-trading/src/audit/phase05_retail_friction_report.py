"""Phase 0.5 deterministic retail-friction reconstruction.

Uses the actual phase05_top5_feasibility.csv schema:
rebalance_date, execution_date, rank, symbol, momentum_raw_unadjusted,
execution_price, price_basis.

For each capital scenario, each selected stock receives a 20% target.
Whole shares are purchased with floor(target/prices); no replacement is allowed.
The remainder is cash. This is a feasibility diagnostic, not a performance backtest.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "audits" / "phase05_top5_feasibility.csv"
OUTPUT = ROOT / "audits" / "phase05_retail_friction_report.csv"

CAPITALS = [20_000, 25_000, 50_000, 100_000, 500_000, 1_000_000]

# Existing Phase 0.5 conservative full-liquidation/rebuild cost-feasibility
# results. These are feasibility assumptions, not realized strategy turnover.
CONSERVATIVE_COST_DRAG = {
    20_000: 0.0329,
    25_000: 0.0297,
    50_000: 0.0233,
    100_000: 0.0201,
    500_000: 0.0176,
    1_000_000: 0.0173,
}


def main() -> None:
    if not INPUT.exists():
        raise SystemExit(f"Missing required artifact: {INPUT}")

    with INPUT.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    required = {
        "rebalance_date",
        "execution_date",
        "rank",
        "symbol",
        "momentum_raw_unadjusted",
        "execution_price",
        "price_basis",
    }
    missing = required - set(rows[0]) if rows else required
    if missing:
        raise SystemExit(f"Unexpected feasibility schema; missing columns: {sorted(missing)}")

    dates = sorted({r["rebalance_date"] for r in rows})
    grouped = {}
    for r in rows:
        grouped.setdefault(r["rebalance_date"], []).append(r)

    # Only dates with exactly five ranked selections are executable Top-5
    # feasibility dates. The known terminal 2025-12-31 row is absent because
    # it has no next trading-day execution.
    selected_dates = []
    for d in dates:
        rr = sorted(grouped[d], key=lambda x: int(x["rank"]))
        if len(rr) == 5 and [int(x["rank"]) for x in rr] == [1, 2, 3, 4, 5]:
            selected_dates.append(d)

    print("PHASE 0.5 RETAIL FRICTION REPORT")
    print(f"Input: {INPUT}")
    print(f"Selection rows: {len(rows)}")
    print(f"Executable Top-5 rebalances: {len(selected_dates)}")

    output = []

    for capital in CAPITALS:
        per_rebalance = []

        for d in selected_dates:
            rr = sorted(grouped[d], key=lambda x: int(x["rank"]))
            target = capital / 5.0

            shares = []
            invested = 0.0
            unbuyable = 0

            for r in rr:
                price = float(r["execution_price"])
                if price <= 0:
                    raise SystemExit(f"Invalid execution price for {d}/{r['symbol']}: {price}")

                n = math.floor(target / price)
                if n < 1:
                    unbuyable += 1
                value = n * price
                invested += value

                shares.append({
                    "symbol": r["symbol"],
                    "price": price,
                    "shares": n,
                    "value": value,
                    "realized_weight": value / capital,
                })

            cash = capital - invested
            cash_weight = cash / capital

            abs_dev = mean(
                abs(x["realized_weight"] - 0.20) for x in shares
            )

            invested_weight = invested / capital

            per_rebalance.append({
                "date": d,
                "cash_weight": cash_weight,
                "invested_weight": invested_weight,
                "abs_weight_deviation": abs_dev,
                "unbuyable_count": unbuyable,
            })

        cash_values = [x["cash_weight"] for x in per_rebalance]
        dev_values = [x["abs_weight_deviation"] for x in per_rebalance]
        invested_values = [x["invested_weight"] for x in per_rebalance]
        unbuy_counts = [x["unbuyable_count"] for x in per_rebalance]

        unbuyable_rebalances = sum(x > 0 for x in unbuy_counts)
        total_unbuyable_slots = sum(unbuy_counts)

        cost_drag = CONSERVATIVE_COST_DRAG[capital]

        # Conservative break-even: gross return must at least cover the
        # modeled cost drag. This is NOT a strategy return forecast.
        break_even = cost_drag

        result = {
            "capital": capital,
            "executable_rebalances": len(per_rebalance),
            "unbuyable_rebalances": unbuyable_rebalances,
            "unbuyable_fraction": unbuyable_rebalances / len(per_rebalance),
            "total_unbuyable_slots": total_unbuyable_slots,
            "mean_cash": mean(cash_values),
            "median_cash": median(cash_values),
            "max_cash": max(cash_values),
            "mean_invested_weight": mean(invested_values),
            "mean_abs_weight_deviation": mean(dev_values),
            "conservative_cost_drag": cost_drag,
            "conservative_break_even_gross_return": break_even,
            "interpretation": "feasibility diagnostic; not strategy performance",
        }
        output.append(result)

        print(
            f"₹{capital:,}: "
            f"unbuyable={unbuyable_rebalances}/{len(per_rebalance)}, "
            f"unbuyable_slots={total_unbuyable_slots}, "
            f"mean_cash={mean(cash_values):.2%}, "
            f"median_cash={median(cash_values):.2%}, "
            f"max_cash={max(cash_values):.2%}, "
            f"mean_invested={mean(invested_values):.2%}, "
            f"mean_abs_dev={mean(dev_values):.2%}, "
            f"conservative_cost={cost_drag:.2%}"
        )

    with OUTPUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=output[0].keys())
        writer.writeheader()
        writer.writerows(output)

    print(f"Wrote: {OUTPUT}")
    print("PASS: deterministic whole-share feasibility report generated.")
    print("No strategy performance return was calculated.")


if __name__ == "__main__":
    main()
