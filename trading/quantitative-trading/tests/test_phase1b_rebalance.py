from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio.rebalance import plan_rebalance


def test_new_selection_buys_whole_share_targets():
    p = plan_rebalance(
        decision_date=date(2025, 3, 31), execution_date=date(2025, 4, 1),
        capital=25000, starting_cash=25000, starting_positions={},
        ranked_symbols=[("AAA",1),("BBB",2),("CCC",3),("DDD",4),("EEE",5)],
        execution_opens={"AAA":100,"BBB":250,"CCC":500,"DDD":1000,"EEE":2000},
    )
    assert [t.shares for t in p.trades] == [50,20,10,5,2]
    # Whole-share targets leave residual cash when a target cannot be filled exactly.
    assert p.retained_unallocated_cash == 1000


def test_unbuyable_name_is_retained_as_cash_without_replacement():
    p = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=25000, starting_positions={},
        ranked_symbols=[("AAA",1),("BBB",2),("CCC",3),("DDD",4),("EEE",5)],
        execution_opens={"AAA":100,"BBB":250,"CCC":500,"DDD":1000,"EEE":6000},
    )
    assert all(t.symbol != "EEE" for t in p.trades)
    assert p.retained_unallocated_cash == 25000 - (50*100 + 20*250 + 10*500 + 5*1000)


def test_selected_name_is_resized_and_deselected_name_is_sold():
    p = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=5000,
        starting_positions={"AAA":20,"OLD":10},
        ranked_symbols=[("AAA",1),("BBB",2)],
        execution_opens={"AAA":100,"BBB":250,"OLD":100},
        holdings=2, target_weight=0.5,
    )
    assert [(t.symbol,t.side,t.shares) for t in p.trades] == [
        ("OLD","SELL",10),("AAA","BUY",105),("BBB","BUY",50)
    ]


def test_missing_selected_open_fails_closed():
    p = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=25000, starting_positions={},
        ranked_symbols=[("AAA",1)], execution_opens={}, holdings=1, target_weight=1.0,
    )
    assert p.blocked
    assert p.block_reason == "MISSING_EXECUTION_OPEN:AAA"
    assert p.trades == ()


def test_missing_sell_open_fails_closed():
    p = plan_rebalance(
        decision_date=date(2025,3,31), execution_date=date(2025,4,1),
        capital=25000, starting_cash=25000, starting_positions={"OLD":10},
        ranked_symbols=[("AAA",1)], execution_opens={"AAA":100},
        holdings=1, target_weight=1.0,
    )
    assert p.blocked
    assert p.block_reason == "MISSING_EXECUTION_OPEN_FOR_SELL:OLD"
