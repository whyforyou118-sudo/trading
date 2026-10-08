"""Tests for execution-open NAV target sizing."""
from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio.accounting import PortfolioState
from portfolio.costs import DeliveryCostModel
from portfolio.simulation import plan_and_execute_at_open


ROOT = Path(__file__).resolve().parents[1]
COSTS = DeliveryCostModel.from_csv(ROOT / "data/reference/zerodha_delivery_cost_schedule.csv")


def test_targets_use_execution_open_pretrade_nav_not_initial_capital():
    state = PortfolioState(cash=10000, positions={"AAA": 10})
    # At the execution open: NAV = ₹10,000 cash + 10 * ₹210 = ₹12,100.
    step = plan_and_execute_at_open(
        state=state,
        decision_date=date(2025, 3, 31),
        execution_date=date(2025, 4, 1),
        ranked_symbols=[("AAA", 1), ("BBB", 2)],
        execution_opens={"AAA": 210, "BBB": 400},
        cost_model=COSTS,
        holdings=2,
        target_weight=0.5,
    )
    assert step.pretrade_nav == pytest.approx(12100)
    assert [t.target_notional for t in step.plan.targets] == [6050, 6050]
    assert step.plan.targets[0].target_shares == 28
    assert step.plan.targets[1].target_shares == 15
    assert step.execution is not None
    assert step.execution.state.positions == {"AAA": 28, "BBB": 15}
    assert step.execution.state.cash >= 0


def test_missing_open_for_existing_holding_fails_closed():
    state = PortfolioState(cash=10000, positions={"OLD": 10})
    # Missing valuation prices are a portfolio-state validation error.
    with pytest.raises(ValueError, match="missing mark price"):
        plan_and_execute_at_open(
            state=state,
            decision_date=date(2025, 3, 31),
            execution_date=date(2025, 4, 1),
            ranked_symbols=[("AAA", 1)],
            execution_opens={"AAA": 100},
            cost_model=COSTS,
            holdings=1,
            target_weight=1.0,
        )


def test_missing_selected_open_returns_blocked_plan():
    state = PortfolioState(cash=25000)
    step = plan_and_execute_at_open(
        state=state,
        decision_date=date(2025, 3, 31),
        execution_date=date(2025, 4, 1),
        ranked_symbols=[("AAA", 1)],
        execution_opens={},
        cost_model=COSTS,
        holdings=1,
        target_weight=1.0,
    )
    assert step.plan.blocked
    assert step.execution is None
