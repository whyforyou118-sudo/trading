from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio.accounting import PortfolioState
from portfolio.costs import DeliveryCostModel
from portfolio.engine import execute_rebalance
from portfolio.rebalance import plan_rebalance


ROOT = Path(__file__).resolve().parents[1]
COSTS = DeliveryCostModel.from_csv(ROOT / "data/reference/zerodha_delivery_cost_schedule.csv")


def test_engine_buys_whole_shares_and_preserves_residual_cash():
    state = PortfolioState(cash=25000)
    plan = plan_rebalance(
        decision_date=date(2025, 3, 31), execution_date=date(2025, 4, 1),
        capital=25000, starting_cash=25000, starting_positions={},
        ranked_symbols=[("AAA",1),("BBB",2),("CCC",3),("DDD",4),("EEE",5)],
        execution_opens={"AAA":100,"BBB":250,"CCC":500,"DDD":1000,"EEE":2000},
    )
    result = execute_rebalance(
        state=state, plan=plan, cost_model=COSTS,
        execution_date=date(2025,4,1),
        mark_prices={"AAA":100,"BBB":250,"CCC":500,"DDD":1000,"EEE":2000},
    )
    assert result.state.positions == {"AAA":50,"BBB":20,"CCC":10,"DDD":5,"EEE":2}
    assert result.state.cash < 1000
    assert result.state.cash > 0
    assert result.total_costs > 0
    assert result.ending_nav < result.starting_nav


def test_engine_sells_before_buys_and_resizes_retained_name():
    state = PortfolioState(cash=5000, positions={"AAA":20, "OLD":10})
    plan = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=8000, starting_cash=5000,
        starting_positions={"AAA":20,"OLD":10},
        ranked_symbols=[("AAA",1),("BBB",2)],
        execution_opens={"AAA":100,"BBB":245,"OLD":100},
        holdings=2, target_weight=0.5,
    )
    result = execute_rebalance(
        state=state, plan=plan, cost_model=COSTS,
        execution_date=date(2025,4,1),
        mark_prices={"AAA":100,"BBB":245,"OLD":100},
    )
    assert result.state.positions["AAA"] == 40
    assert result.state.positions["BBB"] == 16
    assert "OLD" not in result.state.positions
    assert result.trades[0].side == "SELL"


def test_engine_rejects_blocked_plan():
    state = PortfolioState(cash=25000)
    plan = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=25000, starting_positions={},
        ranked_symbols=[("AAA",1)], execution_opens={},
        holdings=1, target_weight=1.0,
    )
    with pytest.raises(ValueError, match="cannot execute blocked"):
        execute_rebalance(
            state=state, plan=plan, cost_model=COSTS,
            execution_date=date(2025,4,1), mark_prices={},
        )


def test_engine_rejects_insufficient_cash_without_silent_resize():
    state = PortfolioState(cash=100)
    plan = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=100, starting_positions={},
        ranked_symbols=[("AAA",1)], execution_opens={"AAA":100},
        holdings=1, target_weight=1.0,
    )
    with pytest.raises(ValueError, match="INSUFFICIENT_CASH"):
        execute_rebalance(
            state=state, plan=plan, cost_model=COSTS,
            execution_date=date(2025,4,1), mark_prices={"AAA":100},
        )


def test_engine_requires_matching_execution_date():
    state = PortfolioState(cash=25000)
    plan = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=25000, starting_positions={},
        ranked_symbols=[("AAA",1)], execution_opens={"AAA":100},
        holdings=1, target_weight=1.0,
    )
    with pytest.raises(ValueError, match="execution date"):
        execute_rebalance(
            state=state, plan=plan, cost_model=COSTS,
            execution_date=date(2025,4,2), mark_prices={"AAA":100},
        )


def test_engine_nav_reconciles_to_cash_plus_marked_positions():
    state = PortfolioState(cash=25000)
    plan = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=25000, starting_positions={},
        ranked_symbols=[("AAA",1)], execution_opens={"AAA":24000},
        holdings=1, target_weight=1.0,
    )
    result = execute_rebalance(
        state=state, plan=plan, cost_model=COSTS,
        execution_date=date(2025,4,1), mark_prices={"AAA":24000},
    )
    expected = result.state.cash + result.state.positions["AAA"] * 24000
    assert result.ending_nav == pytest.approx(expected)
