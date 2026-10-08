"""Integration tests for the V6 rebalance planner, execution engine, and ledger.

These are synthetic accounting tests only; they do not run the historical strategy.
"""
from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio.accounting import Dividend, PortfolioState, Trade, apply_ledger
from portfolio.costs import DeliveryCostModel
from portfolio.engine import execute_rebalance
from portfolio.rebalance import plan_rebalance


ROOT = Path(__file__).resolve().parents[1]
COST_MODEL = DeliveryCostModel.from_csv(
    ROOT / "data/reference/zerodha_delivery_cost_schedule.csv"
)
EXECUTION_DATE = date(2025, 4, 1)


def test_five_name_rebalance_reconciles_nav_to_itemized_costs():
    opens = {"AAA": 900.0, "BBB": 800.0, "CCC": 700.0, "DDD": 600.0, "EEE": 500.0}
    state = PortfolioState(cash=25_000.0)
    plan = plan_rebalance(
        decision_date=date(2025, 3, 31),
        execution_date=EXECUTION_DATE,
        capital=25_000.0,
        starting_cash=25_000.0,
        starting_positions={},
        ranked_symbols=[("AAA", 1), ("BBB", 2), ("CCC", 3), ("DDD", 4), ("EEE", 5)],
        execution_opens=opens,
    )

    result = execute_rebalance(
        state=state,
        plan=plan,
        cost_model=COST_MODEL,
        execution_date=EXECUTION_DATE,
        mark_prices=opens,
    )

    assert result.starting_nav == pytest.approx(25_000.0)
    assert result.state.cash >= 0
    assert result.state.positions == {"AAA": 5, "BBB": 6, "CCC": 7, "DDD": 8, "EEE": 10}
    assert result.total_costs == pytest.approx(sum(t.costs.total for t in result.trades))
    assert result.starting_nav - result.ending_nav == pytest.approx(result.total_costs)
    assert state.cash == pytest.approx(25_000.0)
    assert state.positions == {}


def test_insufficient_cash_fails_closed_without_mutating_input_state():
    # A 100% target leaves no cash reserve for transaction costs.
    opens = {"AAA": 100.0}
    state = PortfolioState(cash=1_000.0)
    plan = plan_rebalance(
        decision_date=date(2025, 3, 31),
        execution_date=EXECUTION_DATE,
        capital=1_000.0,
        starting_cash=1_000.0,
        starting_positions={},
        ranked_symbols=[("AAA", 1)],
        execution_opens=opens,
        holdings=1,
        target_weight=1.0,
    )

    with pytest.raises(ValueError, match="INSUFFICIENT_CASH"):
        execute_rebalance(
            state=state,
            plan=plan,
            cost_model=COST_MODEL,
            execution_date=EXECUTION_DATE,
            mark_prices=opens,
        )

    # Execution works on a copy, so a failed order cannot leak partial state.
    assert state.cash == pytest.approx(1_000.0)
    assert state.positions == {}
    assert state.cumulative_costs.total == pytest.approx(0.0)


def test_same_day_open_trade_does_not_change_dividend_entitlement():
    # Ledger convention: entitlement is determined before same-day trades.
    events = [
        Trade(date="2025-04-01", symbol="AAA", side="BUY", shares=5, price=10.0),
        Dividend(date="2025-04-01", symbol="AAA", per_share=2.0),
    ]

    state = apply_ledger(
        initial_cash=1_000.0,
        events=events,
        initial_positions={"AAA": 10},
    )

    assert state.cumulative_dividends == pytest.approx(20.0)
    assert state.cash == pytest.approx(970.0)
    assert state.positions == {"AAA": 15}


def test_sell_costs_and_proceeds_reconcile_through_ledger():
    sell_costs = COST_MODEL.costs(
        EXECUTION_DATE, "SELL", 2_000.0, scrips_sold=1, slippage=0.001
    )
    trade = Trade(
        date=EXECUTION_DATE.isoformat(),
        symbol="AAA",
        side="SELL",
        shares=20,
        price=100.0,
        costs=sell_costs,
    )
    state = apply_ledger(
        initial_cash=500.0,
        events=[trade],
        initial_positions={"AAA": 20},
    )

    assert state.cash == pytest.approx(500.0 + 2_000.0 - sell_costs.total)
    assert state.positions == {}
    assert state.cumulative_costs.total == pytest.approx(sell_costs.total)
