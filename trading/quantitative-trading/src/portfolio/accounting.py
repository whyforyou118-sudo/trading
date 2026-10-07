"""Transaction-level portfolio accounting engine for Phase 1A.

The ledger is independent of signal generation. It models whole-share trades,
explicit cash, itemized costs, dividends, share-ratio corporate actions, and
mark-to-market NAV.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Dict, Iterable, Mapping, Sequence, Union


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

    def __post_init__(self) -> None:
        values = (self.brokerage, self.stt, self.transaction_charges, self.sebi,
                  self.stamp_duty, self.gst, self.dp_charge, self.slippage)
        if not all(isfinite(float(v)) and v >= 0 for v in values):
            raise ValueError("all transaction costs must be finite and non-negative")

    @property
    def total(self) -> float:
        return sum((self.brokerage, self.stt, self.transaction_charges, self.sebi,
                    self.stamp_duty, self.gst, self.dp_charge, self.slippage))


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
        if isinstance(self.shares, bool) or self.shares <= 0 or int(self.shares) != self.shares:
            raise ValueError("shares must be a positive whole number")
        if not isfinite(float(self.price)) or self.price <= 0:
            raise ValueError("price must be a finite positive number")
        if not self.symbol:
            raise ValueError("symbol cannot be empty")

    @property
    def gross_value(self) -> float:
        return self.shares * self.price

    @property
    def cash_delta(self) -> float:
        return -(self.gross_value + self.costs.total) if self.side == "BUY" else self.gross_value - self.costs.total


@dataclass(frozen=True)
class Dividend:
    date: str
    symbol: str
    per_share: float

    def __post_init__(self) -> None:
        if not isfinite(float(self.per_share)) or self.per_share < 0:
            raise ValueError("per_share must be finite and non-negative")


@dataclass(frozen=True)
class SecurityConversion:
    """Convert one security into another using an integer share ratio.

    Example: 25 old shares -> 42 new shares is numerator=42, denominator=25.
    The conversion is fail-closed if the resulting share count is fractional.
    """
    date: str
    old_symbol: str
    new_symbol: str
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if not self.old_symbol or not self.new_symbol:
            raise ValueError("security symbols cannot be empty")
        if (isinstance(self.numerator, bool) or isinstance(self.denominator, bool)
                or self.numerator <= 0 or self.denominator <= 0
                or int(self.numerator) != self.numerator
                or int(self.denominator) != self.denominator):
            raise ValueError("conversion ratio terms must be positive whole numbers")


@dataclass(frozen=True)
class ShareRatioAction:
    date: str
    symbol: str
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if (isinstance(self.numerator, bool) or isinstance(self.denominator, bool)
                or self.numerator <= 0 or self.denominator <= 0
                or int(self.numerator) != self.numerator
                or int(self.denominator) != self.denominator):
            raise ValueError("share ratio terms must be positive whole numbers")


LedgerEvent = Union[Trade, Dividend, ShareRatioAction, SecurityConversion]


@dataclass
class PortfolioState:
    cash: float
    positions: Dict[str, int] = field(default_factory=dict)
    cumulative_costs: CostBreakdown = field(default_factory=CostBreakdown)
    cumulative_dividends: float = 0.0

    def __post_init__(self) -> None:
        if not isfinite(float(self.cash)):
            raise ValueError("cash must be finite")
        for symbol, qty in self.positions.items():
            if not symbol or isinstance(qty, bool) or qty < 0 or int(qty) != qty:
                raise ValueError("positions must contain non-negative whole shares")

    def shares(self, symbol: str) -> int:
        return self.positions.get(symbol, 0)

    def apply_trade(self, trade: Trade) -> None:
        held = self.shares(trade.symbol)
        if trade.side == "SELL" and trade.shares > held:
            raise ValueError(f"cannot sell {trade.shares} {trade.symbol}; only {held} held")
        self.cash += trade.cash_delta
        if trade.side == "BUY":
            self.positions[trade.symbol] = held + trade.shares
        else:
            remaining = held - trade.shares
            if remaining:
                self.positions[trade.symbol] = remaining
            else:
                self.positions.pop(trade.symbol, None)
        self.cumulative_costs = add_costs(self.cumulative_costs, trade.costs)

    def apply_dividend(self, event: Dividend) -> float:
        credit = self.shares(event.symbol) * event.per_share
        self.cash += credit
        self.cumulative_dividends += credit
        return credit

    def apply_security_conversion(self, event: SecurityConversion) -> None:
        old = self.shares(event.old_symbol)
        numerator = old * event.numerator
        if numerator % event.denominator:
            raise ValueError(
                f"non-integral security conversion for {event.old_symbol} -> {event.new_symbol}"
            )
        new = numerator // event.denominator
        self.positions.pop(event.old_symbol, None)
        if new:
            self.positions[event.new_symbol] = self.shares(event.new_symbol) + new

    def apply_share_ratio(self, event: ShareRatioAction) -> None:
        old = self.shares(event.symbol)
        numerator = old * event.numerator
        if numerator % event.denominator:
            raise ValueError(f"non-integral share result for {event.symbol}")
        new = numerator // event.denominator
        if new:
            self.positions[event.symbol] = new
        else:
            self.positions.pop(event.symbol, None)

    def market_value(self, prices: Mapping[str, float]) -> float:
        missing = [s for s in self.positions if s not in prices]
        if missing:
            raise ValueError(f"missing mark price(s): {missing}")
        invalid = [s for s, p in prices.items() if not isfinite(float(p)) or p <= 0]
        if invalid:
            raise ValueError(f"invalid mark price(s): {invalid}")
        return self.cash + sum(qty * prices[symbol] for symbol, qty in self.positions.items())


def add_costs(a: CostBreakdown, b: CostBreakdown) -> CostBreakdown:
    return CostBreakdown(
        brokerage=a.brokerage + b.brokerage, stt=a.stt + b.stt,
        transaction_charges=a.transaction_charges + b.transaction_charges,
        sebi=a.sebi + b.sebi, stamp_duty=a.stamp_duty + b.stamp_duty,
        gst=a.gst + b.gst, dp_charge=a.dp_charge + b.dp_charge,
        slippage=a.slippage + b.slippage,
    )


def apply_ledger(initial_cash: float, events: Sequence[LedgerEvent]) -> PortfolioState:
    """Replay a complete event ledger in deterministic date/priority order.

    Same-day priority is corporate action, trade, dividend. This makes the
    entitlement convention explicit and deterministic for synthetic tests;
    historical ingestion must encode the source's ex/record-date convention
    before using this function.
    """
    state = PortfolioState(cash=initial_cash)
    priority = {SecurityConversion: 0, ShareRatioAction: 0, Trade: 1, Dividend: 2}
    ordered = sorted(enumerate(events), key=lambda x: (x[1].date, priority[type(x[1])], x[0]))
    for _, event in ordered:
        if isinstance(event, Trade):
            state.apply_trade(event)
        elif isinstance(event, Dividend):
            state.apply_dividend(event)
        elif isinstance(event, SecurityConversion):
            state.apply_security_conversion(event)
        else:
            state.apply_share_ratio(event)
    return state


def reconcile_cash(initial_cash: float, trades: Iterable[Trade], dividends: Iterable[Dividend]) -> float:
    """Replay trades and dividends and return final cash.

    Dividend credits are computed from shares actually held at the event date;
    they are never guessed from a static share count.
    """
    events: list[LedgerEvent] = [*trades, *dividends]
    return apply_ledger(initial_cash, events).cash
