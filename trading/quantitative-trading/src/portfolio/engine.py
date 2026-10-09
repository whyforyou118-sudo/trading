"""Chronological V6 portfolio execution engine.

Connects a deterministic rebalance plan to the transaction-level accounting
ledger. It does not generate signals or alter frozen strategy rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Mapping, Sequence

from .accounting import PortfolioState, Trade, add_costs
from .costs import DeliveryCostModel
from .rebalance import RebalancePlan


@dataclass(frozen=True)
class ExecutionResult:
    state: PortfolioState
    trades: tuple[Trade, ...]
    starting_nav: float
    ending_nav: float
    gross_traded_value: float
    total_costs: float


def mark_to_market(state: PortfolioState, prices: Mapping[str, float]) -> float:
    return state.market_value(prices)


def execute_rebalance(
    *,
    state: PortfolioState,
    plan: RebalancePlan,
    cost_model: DeliveryCostModel,
    execution_date: date,
    mark_prices: Mapping[str, float],
) -> ExecutionResult:
    """Execute one already-validated rebalance plan in chronological order.

    Sells are applied before buys so proceeds can fund purchases. Costs are
    calculated from raw execution-open gross values and include the frozen
    0.10% slippage component. No target shares are silently changed when cash
    is insufficient; execution fails closed instead.
    """
    if plan.blocked:
        raise ValueError(f"cannot execute blocked rebalance: {plan.block_reason}")
    if execution_date != plan.execution_date:
        raise ValueError("execution date does not match rebalance plan")
    if state.cash < 0:
        raise ValueError("starting cash cannot be negative")

    starting_nav = mark_to_market(state, mark_prices)
    if not isfinite(starting_nav) or starting_nav <= 0:
        raise ValueError("starting NAV must be finite and positive")

    working = PortfolioState(
        cash=state.cash,
        positions=dict(state.positions),
        cumulative_costs=state.cumulative_costs,
        cumulative_dividends=state.cumulative_dividends,
        dividend_receivable=state.dividend_receivable,
        pending_dividends=dict(state.pending_dividends),
        applied_event_ids=set(state.applied_event_ids),
    )
    executed: list[Trade] = []
    total_gross = 0.0

    # Deterministic priority: all sells, then buys. Within each side the plan
    # already has deterministic symbol ordering.
    ordered = [t for t in plan.trades if t.side == "SELL"] + [
        t for t in plan.trades if t.side == "BUY"
    ]
    for planned in ordered:
        if planned.shares <= 0:
            continue
        price = float(planned.execution_open)
        if not isfinite(price) or price <= 0:
            raise ValueError(f"invalid execution open: {planned.symbol}")
        gross = planned.shares * price
        costs = cost_model.costs(
            execution_date,
            planned.side,
            gross,
            scrips_sold=1 if planned.side == "SELL" else 0,
        )
        trade = Trade(
            date=execution_date.isoformat(),
            symbol=planned.symbol,
            side=planned.side,
            shares=planned.shares,
            price=price,
            costs=costs,
        )
        if planned.side == "BUY" and working.cash + 1e-9 < gross + costs.total:
            raise ValueError(
                f"INSUFFICIENT_CASH:{planned.symbol}:"
                f"required={gross + costs.total:.10f}:available={working.cash:.10f}"
            )
        working.apply_trade(trade)
        executed.append(trade)
        total_gross += gross

    ending_nav = mark_to_market(working, mark_prices)
    if not isfinite(ending_nav) or ending_nav < 0:
        raise ValueError("ending NAV must be finite and non-negative")

    return ExecutionResult(
        state=working,
        trades=tuple(executed),
        starting_nav=starting_nav,
        ending_nav=ending_nav,
        gross_traded_value=total_gross,
        total_costs=sum(t.costs.total for t in executed),
    )
