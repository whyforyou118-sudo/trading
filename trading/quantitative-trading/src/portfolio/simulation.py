"""Execution-open NAV orchestration for the frozen V6 rebalance contract.

This is a single-rebalance boundary layer. It deliberately does not run a
historical backtest or apply corporate-action/dividend events.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence

from portfolio.accounting import PortfolioState
from portfolio.costs import DeliveryCostModel
from portfolio.engine import ExecutionResult, execute_rebalance, mark_to_market
from portfolio.rebalance import RebalancePlan, plan_rebalance


@dataclass(frozen=True)
class RebalanceStep:
    plan: RebalancePlan
    execution: ExecutionResult | None
    pretrade_nav: float


def plan_and_execute_at_open(
    *,
    state: PortfolioState,
    decision_date: date,
    execution_date: date,
    ranked_symbols: Sequence[tuple[str, int]],
    execution_opens: Mapping[str, float],
    cost_model: DeliveryCostModel,
    target_weight: float = 0.20,
    holdings: int = 5,
) -> RebalanceStep:
    """Plan targets from pre-trade NAV marked at the same day's raw opens.

    `execution_opens` must contain raw, unadjusted opens for every currently
    held security and every selected security. Missing held-name marks fail
    closed through mark_to_market; missing selected/sell execution opens are
    blocked by the planner. No fixed initial capital is reused after inception.
    """
    if execution_date <= decision_date:
        raise ValueError("execution_date must be after decision_date")
    if state.cash < 0:
        raise ValueError("starting cash cannot be negative")
    if not ranked_symbols:
        raise ValueError("empty eligible ranking requires explicit frozen-policy handling")

    # A current holding without a raw open is not assigned a guessed mark.
    pretrade_nav = mark_to_market(state, execution_opens)
    plan = plan_rebalance(
        decision_date=decision_date,
        execution_date=execution_date,
        capital=pretrade_nav,
        starting_cash=state.cash,
        starting_positions=dict(state.positions),
        ranked_symbols=ranked_symbols,
        execution_opens=execution_opens,
        target_weight=target_weight,
        holdings=holdings,
        no_replacement=True,
    )
    if plan.blocked:
        return RebalanceStep(plan=plan, execution=None, pretrade_nav=pretrade_nav)

    execution = execute_rebalance(
        state=state,
        plan=plan,
        cost_model=cost_model,
        execution_date=execution_date,
        mark_prices=execution_opens,
    )
    # Assert the contract for every selected target, including a short list.
    expected_target = pretrade_nav * target_weight
    if any(abs(t.target_notional - expected_target) > 1e-7 for t in plan.targets):
        raise AssertionError("target notional does not equal execution-open NAV weight")
    return RebalanceStep(plan=plan, execution=execution, pretrade_nav=pretrade_nav)
