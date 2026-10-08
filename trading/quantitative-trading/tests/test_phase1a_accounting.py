from pathlib import Path
import sys
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio.accounting import (
    CostBreakdown, Dividend, PortfolioState, SecurityConversion, ShareRatioAction, Trade, apply_ledger,
    reconcile_cash,
)

def test_cash_positions_and_costs_reconcile():
    p = PortfolioState(cash=10_000.0)
    c = CostBreakdown(brokerage=1.0, stt=2.0, gst=0.54)
    p.apply_trade(Trade("2025-01-01", "AAA", "BUY", 10, 100.0, c))
    assert p.shares("AAA") == 10
    assert abs(p.cash - (10_000 - 1_000 - c.total)) < 1e-9

def test_dividend_and_split_preserve_economic_value():
    p = PortfolioState(cash=0.0, positions={"AAA": 10})
    before = p.market_value({"AAA": 100.0})
    p.apply_dividend(Dividend("2025-01-02", "AAA", 5.0))
    p.apply_share_ratio(ShareRatioAction("2025-01-03", "AAA", 2, 1))
    after = p.market_value({"AAA": 50.0})
    assert abs(after - (before + 50.0)) < 1e-9

def test_complete_ledger_uses_event_date_shares():
    trades = [
        Trade("2025-01-01", "AAA", "BUY", 10, 100.0),
        Trade("2025-01-04", "AAA", "SELL", 4, 110.0),
    ]
    dividends = [Dividend("2025-01-03", "AAA", 5.0)]
    assert abs(reconcile_cash(1000.0, trades, dividends) - 490.0) < 1e-9

def test_split_then_trade_is_replayed_in_date_order():
    events = [
        Trade("2025-01-04", "AAA", "SELL", 20, 50.0),
        ShareRatioAction("2025-01-02", "AAA", 2, 1),
        Trade("2025-01-01", "AAA", "BUY", 10, 100.0),
    ]
    state = apply_ledger(0.0, events)
    assert state.shares("AAA") == 0
    assert abs(state.cash - 0.0) < 1e-9

def test_oversell_and_fractional_shares_fail_closed():
    p = PortfolioState(cash=0.0, positions={"AAA": 5})
    try:
        p.apply_trade(Trade("2025-01-04", "AAA", "SELL", 6, 100.0))
    except ValueError:
        pass
    else:
        raise AssertionError("oversell must fail")
    try:
        Trade("2025-01-04", "AAA", "BUY", 1.5, 100.0)
    except ValueError:
        pass
    else:
        raise AssertionError("fractional shares must fail")


def test_security_conversion_uses_production_ledger_path():
    state = apply_ledger(
        0.0,
        [
            Trade("2020-01-01", "HDFC", "BUY", 25, 100.0),
            SecurityConversion("2020-02-01", "HDFC", "HDFCBANK", 42, 25),
        ],
    )
    assert state.shares("HDFC") == 0
    assert state.shares("HDFCBANK") == 42


def test_security_conversion_rejects_fractional_result():
    with pytest.raises(ValueError):
        apply_ledger(
            0.0,
            [
                Trade("2020-01-01", "OLD", "BUY", 1, 100.0),
                SecurityConversion("2020-02-01", "OLD", "NEW", 1, 2),
            ],
        )

def test_ex_date_dividend_precedes_same_day_open_trade():
    state = apply_ledger(
        0.0,
        [
            Trade("2020-01-01", "ABC", "BUY", 10, 100.0),
            Dividend("2020-01-02", "ABC", 5.0),
            Trade("2020-01-02", "ABC", "SELL", 10, 101.0),
        ],
    )
    assert state.cash == 60.0
    assert state.shares("ABC") == 0
    assert state.cumulative_dividends == 50.0
