"""Date-effective Zerodha equity-delivery cost model from the frozen repository schedule."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from portfolio.accounting import CostBreakdown


@dataclass(frozen=True)
class CostScheduleRow:
    effective_from: date
    effective_to: date
    brokerage_pct: float
    brokerage_fixed: float
    stt_buy_pct: float
    stt_sell_pct: float
    transaction_charge_pct: float
    sebi_per_crore: float
    stamp_buy_pct: float
    gst_pct: float
    dp_per_scrip: float

    def contains(self, d: date) -> bool:
        return self.effective_from <= d <= self.effective_to


class DeliveryCostModel:
    def __init__(self, rows: list[CostScheduleRow]):
        self.rows = sorted(rows, key=lambda r: r.effective_from)
        if not self.rows:
            raise ValueError("cost schedule cannot be empty")

    @classmethod
    def from_csv(cls, path: Path) -> "DeliveryCostModel":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = []
            for r in csv.DictReader(f):
                if r.get("verified", "").strip().upper() != "TRUE":
                    raise ValueError("unverified cost schedule row")
                rows.append(CostScheduleRow(
                    date.fromisoformat(r["effective_from"]),
                    date.fromisoformat(r["effective_to"]),
                    float(r["brokerage_pct"]), float(r["brokerage_fixed"]),
                    float(r["stt_buy_pct"]), float(r["stt_sell_pct"]),
                    float(r["transaction_charge_pct"]), float(r["sebi_per_crore"]),
                    float(r["stamp_buy_pct"]), float(r["gst_pct"]),
                    float(r["dp_per_scrip"]),
                ))
        return cls(rows)

    def row(self, d: date) -> CostScheduleRow:
        matches = [r for r in self.rows if r.contains(d)]
        if len(matches) != 1:
            raise ValueError(f"cost schedule must have exactly one row for {d}; found {len(matches)}")
        return matches[0]

    def costs(self, d: date, side: str, gross_value: float, *, scrips_sold: int = 0,
              slippage: float = 0.001) -> CostBreakdown:
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if gross_value <= 0:
            raise ValueError("gross_value must be positive")
        if scrips_sold < 0:
            raise ValueError("scrips_sold must be non-negative")
        r = self.row(d)
        p = lambda x: x / 100.0
        brokerage = gross_value * p(r.brokerage_pct) + r.brokerage_fixed
        stt = gross_value * p(r.stt_buy_pct if side == "BUY" else r.stt_sell_pct)
        transaction = gross_value * p(r.transaction_charge_pct)
        sebi = gross_value / 1e7 * r.sebi_per_crore
        stamp = gross_value * p(r.stamp_buy_pct) if side == "BUY" else 0.0
        dp = r.dp_per_scrip * scrips_sold if side == "SELL" else 0.0
        gst = (brokerage + transaction + sebi + dp) * p(r.gst_pct)
        slip = gross_value * slippage
        return CostBreakdown(
            brokerage=brokerage, stt=stt, transaction_charges=transaction,
            sebi=sebi, stamp_duty=stamp, gst=gst, dp_charge=dp, slippage=slip,
        )
