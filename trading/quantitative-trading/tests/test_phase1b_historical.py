"""Regression tests for chronological historical portfolio orchestration."""
from datetime import date
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio.accounting import (
    DividendEntitlement,
    DividendPayment,
    PortfolioState,
)
from portfolio.costs import DeliveryCostModel
from portfolio.historical import (
    HistoricalEvent,
    HistoricalRunBlocked,
    RebalanceInstruction,
    RightsLifecycle,
    SessionPrices,
    run_historical_simulation,
)
from portfolio.rights import RightsEntitlement


COSTS = DeliveryCostModel.from_csv(ROOT / "data/reference/zerodha_delivery_cost_schedule.csv")
D1 = date(2024, 3, 28)
E1 = date(2024, 4, 1)
RDATE = date(2024, 4, 10)
RIGHTS_DATE = date(2024, 4, 15)
D2 = date(2024, 6, 28)
E2 = date(2024, 7, 1)
SYMBOLS = ("AAA", "BBB", "CCC", "DDD", "EEE")
RANKED = tuple((symbol, i) for i, symbol in enumerate(SYMBOLS, 1))


def _session(opens, closes=None):
    return SessionPrices(opens=dict(opens), closes=dict(closes if closes is not None else opens))


def _prices():
    base = {"AAA": 900.0, "BBB": 800.0, "CCC": 700.0, "DDD": 600.0, "EEE": 500.0}
    moved = {"AAA": 920.0, "BBB": 810.0, "CCC": 710.0, "DDD": 610.0, "EEE": 510.0}
    return {
        D1: _session(base),
        E1: _session(base),
        RDATE: _session({"AAA": 910.0}),
        RIGHTS_DATE: _session({"AAA": 915.0, "AAA-RE": 10.0}),
        D2: _session(moved),
        E2: _session(moved, closes=moved),
    }


def _instructions():
    return (
        RebalanceInstruction(D1, E1, RANKED),
        RebalanceInstruction(D2, E2, RANKED),
    )


def test_dividend_entitlement_is_receivable_until_payment_date():
    state = PortfolioState(cash=1000.0, positions={"AAA": 10})
    entitlement = DividendEntitlement(
        event_id="DIV-EX-1",
        date="2024-04-10",
        symbol="AAA",
        per_share=2.0,
        payment_date="2024-06-15",
        source_ref="issuer filing: DIV-EX-1",
    )
    payment = DividendPayment(
        event_id="DIV-PAY-1",
        date="2024-06-15",
        entitlement_event_id="DIV-EX-1",
        source_ref="issuer payment notice: DIV-PAY-1",
    )

    assert state.apply_dividend_entitlement(entitlement) == pytest.approx(20.0)
    assert state.cash == pytest.approx(1000.0)
    assert state.dividend_receivable == pytest.approx(20.0)
    assert state.market_value({"AAA": 100.0}) == pytest.approx(2020.0)

    assert state.apply_dividend_payment(payment) == pytest.approx(20.0)
    assert state.cash == pytest.approx(1020.0)
    assert state.dividend_receivable == pytest.approx(0.0)
    assert state.market_value({"AAA": 100.0}) == pytest.approx(2020.0)


def test_historical_runner_rebalances_chronologically_and_renounces_rights_once():
    entitlement = RightsEntitlement(
        date=RDATE.isoformat(),
        parent_symbol="AAA",
        re_symbol="AAA-RE",
        numerator=1,
        denominator=1,
    )
    rights = RightsLifecycle(
        event_id="RIGHTS-AAA-1",
        entitlement=entitlement,
        first_tradable_date=RIGHTS_DATE,
        expected_first_tradable_open=10.0,
        source_ref="official rights price archive: AAA-RE",
        verified=True,
    )
    div_ent = DividendEntitlement(
        event_id="DIV-AAA-1",
        date=RDATE.isoformat(),
        symbol="AAA",
        per_share=2.0,
        payment_date="2024-06-15",
        source_ref="issuer dividend declaration",
    )
    div_pay = DividendPayment(
        event_id="DIV-AAA-PAY-1",
        date="2024-06-15",
        entitlement_event_id="DIV-AAA-1",
        source_ref="issuer dividend payment notice",
    )
    result = run_historical_simulation(
        trading_dates=(D1, E1, RDATE, RIGHTS_DATE, D2, E2),
        session_prices=_prices(),
        rebalances=_instructions(),
        events=(
            HistoricalEvent("DIV-AAA-1", div_ent.source_ref, div_ent, True),
            HistoricalEvent("DIV-AAA-PAY-1", div_pay.source_ref, div_pay, True),
        ),
        rights_lifecycles=(rights,),
        cost_model=COSTS,
    )

    assert len(result.rebalances) == 2
    assert result.final_nav > 0
    assert result.final_state.cash >= 0
    assert result.final_state.shares("AAA-RE") == 0
    assert "RIGHTS-AAA-1:RENOUNCE" in result.events_applied
    assert sum(t.symbol == "AAA-RE" and t.side == "SELL" for t in result.trades) == 1
    rights_trade = next(t for t in result.trades if t.symbol == "AAA-RE")
    assert rights_trade.price == pytest.approx(10.0)
    assert rights_trade.costs.slippage == pytest.approx(5 * 10.0 * 0.001)
    assert result.final_state.dividend_receivable == pytest.approx(0.0)
    assert result.final_state.cumulative_dividends > 0


def test_historical_runner_rejects_legacy_ex_date_cash_credit():
    from portfolio.accounting import Dividend

    legacy = Dividend(date=RDATE.isoformat(), symbol="AAA", per_share=1.0)
    with pytest.raises(ValueError, match="legacy Dividend"):
        HistoricalEvent("DIV-LEGACY", "unacceptable legacy event", legacy, True)


def test_historical_runner_fails_closed_on_unverified_event():
    event = DividendEntitlement(
        event_id="DIV-UNVERIFIED",
        date=RDATE.isoformat(),
        symbol="AAA",
        per_share=1.0,
        payment_date="2024-06-15",
        source_ref="issuer declaration",
    )
    with pytest.raises(HistoricalRunBlocked, match="unverified historical event"):
        HistoricalEvent("DIV-UNVERIFIED", "issuer declaration", event, False)


def test_historical_runner_fails_closed_if_rights_open_does_not_match_verified_source():
    entitlement = RightsEntitlement(
        date=RDATE.isoformat(), parent_symbol="AAA", re_symbol="AAA-RE",
        numerator=1, denominator=1,
    )
    rights = RightsLifecycle(
        event_id="RIGHTS-MISMATCH",
        entitlement=entitlement,
        first_tradable_date=RIGHTS_DATE,
        expected_first_tradable_open=11.0,
        source_ref="official source says 11.00",
        verified=True,
    )
    with pytest.raises(HistoricalRunBlocked, match="rights raw open mismatch"):
        run_historical_simulation(
            trading_dates=(D1, E1, RDATE, RIGHTS_DATE, D2, E2),
            session_prices=_prices(),
            rebalances=_instructions(),
            events=(),
            rights_lifecycles=(rights,),
            cost_model=COSTS,
        )


def test_historical_runner_rejects_missing_dividend_payment_before_end():
    entitlement = DividendEntitlement(
        event_id="DIV-MISSING-PAY",
        date=RDATE.isoformat(),
        symbol="AAA",
        per_share=1.0,
        payment_date="2024-06-15",
        source_ref="issuer declaration",
    )
    with pytest.raises(HistoricalRunBlocked, match="missing dividend payment"):
        run_historical_simulation(
            trading_dates=(D1, E1, RDATE, RIGHTS_DATE, D2, E2),
            session_prices=_prices(),
            rebalances=_instructions(),
            events=(HistoricalEvent(entitlement.event_id, entitlement.source_ref, entitlement, True),),
            rights_lifecycles=(),
            cost_model=COSTS,
        )


def test_historical_runner_requires_next_actual_trading_day_execution():
    bad = RebalanceInstruction(D1, D2, RANKED)
    with pytest.raises(HistoricalRunBlocked, match="next actual trading session"):
        run_historical_simulation(
            trading_dates=(D1, E1, RDATE, RIGHTS_DATE, D2, E2),
            session_prices=_prices(),
            rebalances=(bad,),
            events=(),
            rights_lifecycles=(),
            cost_model=COSTS,
        )
