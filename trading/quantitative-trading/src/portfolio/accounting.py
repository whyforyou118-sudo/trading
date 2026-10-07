"""Transaction-level portfolio accounting engine for Phase 1A.

This module is deliberately independent of signal generation. It models:
- whole-share trades;
- explicit cash;
- itemized transaction costs;
- separate dividend cash credits;
- stock split/share-ratio corporate actions;
- mark-to-market NAV.

No performance assumptions or strategy selection logic live here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping


@dataclass(frozen=True)
class CostBreakdown:
    brokerage: float = 0.0
    stt: float = 0.0
    transaction_charges: float = 0.0
    sebi: float = 0.0
    stamp_duty: float = 0.0
    gst: float = 0.0
    dp_charge: float = 0.0
    slippage: float = 0.0

    @property
    def total(self) -> float:
        return sum((
            self.brokerage, self.stt, self.transaction_charges, self.sebi,
            self.stamp_duty, self.gst, self.dp_charge, self.slippage,
        ))


@dataclass(frozen=True)
class Trade:
    date: str
    symbol: str
    side: str
    shares: int
    price: float
    costs: CostBreakdown = field(default_factory=CostBreakdown)

    def __post_init__(self) -> None:
        if self.side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if self.shares <= 0 or int(self.shares) != self.shares:
            raise ValueError("shares must be a positive whole number")
        if self.price <= 0:
            raise ValueError("price must be positive")

    @property
    def gross_value(self) -> float:
        return self.shares * self.price

    @property
    def cash_delta(self) -> float:
        if self.side == "BUY":
            return -(self.gross_value + self.costs.total)
        return self.gross_value - self.costs.total


@dataclass(frozen=True)
class Dividend:
    date: str
    symbol: str
    per_share: float

    def __post_init__(self) -> None:
        if self.per_share < 0:
            raise ValueError("per_share cannot be negative")


@dataclass(frozen=True)
class ShareRatioAction:
    """Share-count action such as a stock split/bonus represented by ratio.

    new_shares = old_shares * numerator / denominator.
    No cash is created by the share-count transformation itself.
    """
    date: str
    symbol: str
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator <= 0 or self.denominator <= 0:
            raise ValueError("share ratio terms must be positive")


@dataclass
class PortfolioState:
    cash: float
    positions: Dict[str, int] = field(default_factory=dict)
    cumulative_costs: CostBreakdown = field(default_factory=CostBreakdown)
    cumulative_dividends: float = 0.0

    def shares(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def apply_trade(self, trade: Trade) -> None:
        held = self.positions.get(trade.symbol, 0)
        if trade.side == "BUY":
            self.positions[trade.symbol] = held + trade.shares
        else:
            if trade.shares > held:
                raise ValueError(
                    f"cannot sell {trade.shares} {trade.symbol}; only {held} held"
                )
            remaining = held - trade.shares
            if remaining:
                self.positions[trade.symbol] = remaining
            else:
                self.positions.pop(trade.symbol, None)

        self.cash += trade.cash_delta
        self.cumulative_costs = add_costs(self.cumulative_costs, trade.costs)

    def apply_dividend(self, event: Dividend) -> float:
        qty = self.shares(event.symbol)
        credit = qty * event.per_share
        self.cash += credit
        self.cumulative_dividends += credit
        return credit

    def apply_share_ratio(self, event: ShareRatioAction) -> None:
        old = self.shares(event.symbol)
        numerator = old * event.numerator
        if numerator % event.denominator:
            raise ValueError(
                f"non-integral share result for {event.symbol}: "
                f"{old} * {event.numerator}/{event.denominator}"
            )
        new = numerator // event.denominator
        if new:
            self.positions[event.symbol] = new
        else:
            self.positions.pop(event.symbol, None)

    def market_value(self, prices: Mapping[str, float]) -> float:
        missing = [s for s in self.positions if s not in prices]
        if missing:
            raise ValueError(f"missing mark price(s): {missing}")
        invalid = [s for s, p in prices.items() if p <= 0]
        if invalid:
            raise ValueError(f"non-positive mark price(s): {invalid}")
        return self.cash + sum(
            qty * prices[symbol] for symbol, qty in self.positions.items()
        )


def add_costs(a: CostBreakdown, b: CostBreakdown) -> CostBreakdown:
    return CostBreakdown(
        brokerage=a.brokerage + b.brokerage,
        stt=a.stt + b.stt,
        transaction_charges=a.transaction_charges + b.transaction_charges,
        sebi=a.sebi + b.sebi,
        stamp_duty=a.stamp_duty + b.stamp_duty,
        gst=a.gst + b.gst,
        dp_charge=a.dp_charge + b.dp_charge,
        slippage=a.slippage + b.slippage,
    )


def reconcile_cash(
    initial_cash: float,
    trades: Iterable[Trade],
    dividends: Iterable[Dividend],
) -> float:
    """Independent cash reconciliation from the event ledger."""
    cash = initial_cash
    for trade in trades:
        cash += trade.cash_delta
    for dividend in dividends:
        # Caller must provide dividend amounts as explicit cash credits in the
        # ledger; this helper is intended for events whose shares are known
        # before the credit is generated.
        raise ValueError(
            "Use PortfolioState.apply_dividend for share-dependent dividend credits"
        )
    return cash
