"""Deterministic Phase 0.5/Phase 1A retail-capital arithmetic.

Reads the generated Phase 0.5 Top-5 feasibility artifact and reports the
₹25,000 target-slot arithmetic without using performance returns.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "audits/phase05_top5_feasibility.csv"
DEFAULT_FRICTION = ROOT / "audits/phase05_retail_friction_report.csv"


def pct(x: float) -> str:
    return f"{100.0 * x:.2f}%"


def _parse_count(value: str) -> tuple[int, int | None]:
    """Parse a count encoded as N or N/D without assuming a denominator."""
    raw = str(value).strip()
    if "/" not in raw:
        return int(raw), None
    numerator, denominator = raw.split("/", 1)
    return int(numerator), int(denominator)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selection", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--friction", type=Path, default=DEFAULT_FRICTION)
    ap.add_argument("--capital", type=float, default=25000.0)
    ap.add_argument("--holdings", type=int, default=5)
    args = ap.parse_args()

    target = args.capital / args.holdings
    print("PHASE 1A ₹25K CAPITAL ARITHMETIC")
    print(f"Capital: ₹{args.capital:,.0f}")
    print(f"Holdings target: {args.holdings}")
    print(f"Target per selected stock: ₹{target:,.2f}")

    if args.selection.exists():
        with args.selection.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        # Accept common whole-share feasibility schemas without inventing
        # missing fields. The builder's artifact is the authoritative input.
        price_fields = ("execution_open", "next_open", "price", "execution_price")
        price_field = next((x for x in price_fields if rows and x in rows[0]), None)
        if price_field:
            selected = [r for r in rows if str(r.get("selected", "true")).lower() in {"true", "1", "yes", ""}]
            prices = []
            for r in selected:
                try:
                    prices.append(float(r[price_field]))
                except (TypeError, ValueError):
                    pass
            if prices:
                unbuyable = sum(p > target for p in prices)
                print(f"Selected rows with usable execution prices: {len(prices)}")
                print(f"₹{target:,.0f} cannot buy one share: {unbuyable}/{len(prices)} = {pct(unbuyable/len(prices))}")
            else:
                print("No usable execution-price column/values; frequency must be read from the friction artifact.")
        else:
            print("No recognized execution-price column; frequency must be read from the friction artifact.")
    else:
        print(f"Selection artifact not present: {args.selection}")

    if args.friction.exists():
        with args.friction.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        row = next((r for r in rows if float(r.get("capital", "nan")) == args.capital), None)
        if row:
            print("Friction artifact row:")
            for key in ("unbuyable_rebalances", "unbuyable_slots", "mean_cash_pct",
                        "median_cash_pct", "max_cash_pct", "mean_invested_pct",
                        "mean_abs_weight_deviation_pct", "conservative_cost_drag_pct"):
                if key in row:
                    print(f"  {key}: {row[key]}")
            if "unbuyable_rebalances" in row:
                n, d = _parse_count(row["unbuyable_rebalances"])
                if d is None:
                    # The artifact may store only the numerator. Use an
                    # explicit total_rebalances field when available; never
                    # invent a denominator from a hard-coded assumption.
                    total_raw = row.get("total_rebalances", "")
                    if total_raw:
                        _, d = _parse_count(total_raw)
                    if d is None:
                        print(f"Unbuyable rebalance count: {n} (denominator not present in artifact)")
                    else:
                        print(f"Unbuyable rebalance frequency: {n}/{d} = {pct(n/d)}")
                else:
                    print(f"Unbuyable rebalance frequency: {n}/{d} = {pct(n/d)}")
            if "unbuyable_slots" in row:
                slots = int(row["unbuyable_slots"])
                total_slots_raw = row.get("total_selected_slots", "")
                if total_slots_raw:
                    _, total_slots = _parse_count(total_slots_raw)
                else:
                    total_slots = None
                if total_slots:
                    print(f"Unbuyable selected slots: {slots}/{total_slots} = {pct(slots/total_slots)}")
                else:
                    print(f"Unbuyable selected slots: {slots} (denominator not present in artifact)")
            if "conservative_cost_drag_pct" in row:
                print(f"Conservative transaction-cost break-even anchor: {row['conservative_cost_drag_pct']}%")
                print("This is a full-liquidation/rebuild cost-only anchor, not realized strategy turnover.")
        else:
            print(f"No friction row found for capital ₹{args.capital:,.0f}.")
    else:
        print(f"Friction artifact not present: {args.friction}")

    print("Residual cash is an exposure/opportunity-cost effect, not a transaction charge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
