"""Deterministic V6 whole-share quarterly rebalance planner.

This module plans trades; it does not mutate the accounting ledger and it does
not calculate strategy performance. Execution prices are raw, unadjusted opens.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Target:
    symbol: str
    rank: int
    execution_open: float
    target_notional: float

    @property
    def target_shares(self) -> int:
        return floor(self.target_notional / self.execution_open)


@dataclass(frozen=True)
class PlannedTrade:
    symbol: str
    side: str
    shares: int
    execution_open: float

    @property
    def gross_value(self) -> float:
        return self.shares * self.execution_open


@dataclass(frozen=True)
class RebalancePlan:
    decision_date: object
    execution_date: object
    starting_cash: float
    starting_positions: Mapping[str, int]
    targets: Sequence[Target]
    trades: Sequence[PlannedTrade]
    retained_unallocated_cash: float
    blocked: bool = False
    block_reason: str = ""


def plan_rebalance(
    *,
    decision_date,
    execution_date,
    capital: float,
    starting_cash: float,
    starting_positions: Mapping[str, int],
    ranked_symbols: Sequence[tuple[str, int]],
    execution_opens: Mapping[str, float],
    target_weight: float = 0.20,
    holdings: int = 5,
    no_replacement: bool = True,
) -> RebalancePlan:
    """Create the exact whole-share target-resize plan for one rebalance.

    A selected symbol with no execution open is a fail-closed block. A selected
    symbol whose target notional cannot buy one whole share becomes cash under
    the frozen NO_REPLACEMENT_RETAIN_CASH policy. Existing non-selected names
    are sold to zero. Selected names are resized directly to target shares.
    """
    if capital <= 0 or starting_cash < 0:
        raise ValueError("capital must be positive and starting_cash non-negative")
    if holdings <= 0 or len(ranked_symbols) > holdings:
        raise ValueError("invalid holdings/ranked_symbols")
    if abs(target_weight * holdings - 1.0) > 1e-9:
        raise ValueError("target_weight must sum to 100% across holdings")

    missing = [s for s, _ in ranked_symbols if s not in execution_opens]
    if missing:
        return RebalancePlan(
            decision_date, execution_date, starting_cash, dict(starting_positions),
            (), (), starting_cash, True,
            "MISSING_EXECUTION_OPEN:" + ",".join(missing),
        )

    targets = []
    target_shares = {}
    for symbol, rank in ranked_symbols:
        price = float(execution_opens[symbol])
        if price <= 0:
            return RebalancePlan(
                decision_date, execution_date, starting_cash, dict(starting_positions),
                (), (), starting_cash, True, f"INVALID_EXECUTION_OPEN:{symbol}",
            )
        t = Target(symbol, rank, price, capital * target_weight)
        targets.append(t)
        # Frozen policy: no replacement when one share cannot be bought.
        target_shares[symbol] = t.target_shares

    trades: list[PlannedTrade] = []
    selected = set(target_shares)
    # First remove positions that are no longer selected.
    for symbol, held in sorted(starting_positions.items()):
        if symbol not in selected and held > 0:
            price = float(execution_opens.get(symbol, 0.0))
            if price <= 0:
                return RebalancePlan(
                    decision_date, execution_date, starting_cash, dict(starting_positions),
                    targets, (), starting_cash, True,
                    f"MISSING_EXECUTION_OPEN_FOR_SELL:{symbol}",
                )
            trades.append(PlannedTrade(symbol, "SELL", held, price))

    # Then resize selected names directly to their target whole-share counts.
    for t in targets:
        held = int(starting_positions.get(t.symbol, 0))
        delta = t.target_shares - held
        if delta > 0:
            trades.append(PlannedTrade(t.symbol, "BUY", delta, t.execution_open))
        elif delta < 0:
            trades.append(PlannedTrade(t.symbol, "SELL", -delta, t.execution_open))

    # This is a planning invariant only; final cash is resolved after actual
    # transaction costs. Unallocated target capital is deliberately retained.
    target_investment = sum(t.target_shares * t.execution_open for t in targets)
    retained = capital - target_investment
    return RebalancePlan(
        decision_date, execution_date, starting_cash, dict(starting_positions),
        tuple(targets), tuple(trades), retained,
    )
