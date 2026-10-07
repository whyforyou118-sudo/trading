"""Phase 1A deterministic accounting/invariant tests.

Synthetic tests only. No historical strategy returns are used.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from portfolio.accounting import (  # noqa: E402
    CostBreakdown,
    Dividend,
    PortfolioState,
    ShareRatioAction,
    Trade,
)


def approx(a: float, b: float, eps: float = 1e-9) -> None:
    assert abs(a - b) <= eps, (a, b)


def test_buy_cash_and_cost_reconcile() -> None:
    p = PortfolioState(cash=10_000.0)
    c = CostBreakdown(brokerage=1.0, stt=2.0, gst=0.54)
    t = Trade("2025-01-01", "AAA", "BUY", 10, 100.0, c)
    p.apply_trade(t)

    approx(p.cash, 10_000 - 1_000 - c.total)
    assert p.shares("AAA") == 10
    approx(p.market_value({"AAA": 100.0}), 10_000 - c.total)


def test_sell_cash_and_cost_reconcile() -> None:
    p = PortfolioState(cash=0.0, positions={"AAA": 10})
    c = CostBreakdown(stt=1.0, dp_charge=13.0)
    t = Trade("2025-01-02", "AAA", "SELL", 10, 120.0, c)
    p.apply_trade(t)

    assert p.shares("AAA") == 0
    approx(p.cash, 1_200 - c.total)
    approx(p.market_value({}), 1_200 - c.total)


def test_dividend_is_separate_cash_credit() -> None:
    p = PortfolioState(cash=0.0, positions={"AAA": 10})
    credit = p.apply_dividend(Dividend("2025-01-03", "AAA", 5.0))

    approx(credit, 50.0)
    approx(p.cash, 50.0)
    assert p.shares("AAA") == 10
    assert p.cumulative_dividends == 50.0


def test_split_preserves_economic_value_when_price_is_adjusted() -> None:
    p = PortfolioState(cash=0.0, positions={"AAA": 10})
    before = p.market_value({"AAA": 100.0})

    p.apply_share_ratio(ShareRatioAction("2025-01-04", "AAA", 2, 1))
    after = p.market_value({"AAA": 50.0})

    assert p.shares("AAA") == 20
    approx(before, after)


def test_raw_price_plus_dividend_not_double_counted() -> None:
    p = PortfolioState(cash=0.0, positions={"AAA": 10})

    # Raw ex-dividend price stays at 100 in this synthetic invariant.
    # The dividend is credited separately as cash exactly once.
    before = p.market_value({"AAA": 100.0})
    p.apply_dividend(Dividend("2025-01-05", "AAA", 5.0))
    after = p.market_value({"AAA": 100.0})

    approx(after - before, 50.0)
    assert p.cumulative_dividends == 50.0


def test_cannot_oversell() -> None:
    p = PortfolioState(cash=0.0, positions={"AAA": 5})
    try:
        p.apply_trade(Trade("2025-01-06", "AAA", "SELL", 6, 100.0))
    except ValueError:
        return
    raise AssertionError("oversell must fail closed")


def test_whole_share_only() -> None:
    p = PortfolioState(cash=1_000.0)
    try:
        p.apply_trade(Trade("2025-01-07", "AAA", "BUY", 1.5, 100.0))  # type: ignore[arg-type]
    except ValueError:
        return
    raise AssertionError("fractional shares must fail closed")


if __name__ == "__main__":
    tests = [
        test_buy_cash_and_cost_reconcile,
        test_sell_cash_and_cost_reconcile,
        test_dividend_is_separate_cash_credit,
        test_split_preserves_economic_value_when_price_is_adjusted,
        test_raw_price_plus_dividend_not_double_counted,
        test_cannot_oversell,
        test_whole_share_only,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"ACCOUNTING INVARIANTS: PASS — {len(tests)} synthetic tests")
