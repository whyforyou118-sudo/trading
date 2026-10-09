from datetime import date
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data.prices import load_raw_instrument_close_by_isin
from strategy.corporate_action_signal import (
    BRITANNIA_DEBENTURE_EVENTS,
    adjust_signal_price_maps,
)


EVENT_2019 = BRITANNIA_DEBENTURE_EVENTS[0]
EVENT_2021 = BRITANNIA_DEBENTURE_EVENTS[1]


def point(day: str, close: float):
    return SimpleNamespace(date=date.fromisoformat(day), close=close)


def test_primary_policy_back_adjusts_only_pre_ex_date_signal_price():
    start, end, audit = adjust_signal_price_maps(
        date(2019, 8, 30),
        {"BRITANNIA": point("2018-08-31", 3000.0)},
        {"BRITANNIA": point("2019-08-30", 2900.0)},
        policy="provisional_face_value",
        parent_ex_date_closes={EVENT_2019.event_id: 2900.0},
    )

    factor = 2900.0 / (2900.0 + 30.0)
    assert start["BRITANNIA"].close == pytest.approx(3000.0 * factor)
    assert end["BRITANNIA"].close == pytest.approx(2900.0)
    applied = next(row for row in audit if row["event_id"] == EVENT_2019.event_id)
    assert applied["applied"] is True
    assert applied["distribution_value_source"] == "PROVISIONAL_FACE_VALUE"
    assert applied["factor_applied_to_pre_event_equity_prices"] == pytest.approx(factor)


def test_no_future_event_information_is_used_before_ex_date():
    start, end, audit = adjust_signal_price_maps(
        date(2019, 8, 21),
        {"BRITANNIA": point("2018-08-31", 3000.0)},
        {"BRITANNIA": point("2019-08-21", 2950.0)},
        policy="provisional_face_value",
        parent_ex_date_closes={},
    )

    assert start["BRITANNIA"].close == pytest.approx(3000.0)
    assert end["BRITANNIA"].close == pytest.approx(2950.0)
    row = next(item for item in audit if item["event_id"] == EVENT_2019.event_id)
    assert row["applied"] is False
    assert row["reason"] == "EVENT_NOT_YET_OCCURRED"


def test_listing_only_policy_does_not_backfill_quote_before_listing_date():
    start, _, audit = adjust_signal_price_maps(
        date(2019, 9, 30),
        {"BRITANNIA": point("2018-08-31", 3000.0)},
        {"BRITANNIA": point("2019-09-30", 2800.0)},
        policy="listing_only",
        parent_ex_date_closes={EVENT_2019.event_id: 2800.0},
        listing_debenture_closes={},
    )

    assert start["BRITANNIA"].close == pytest.approx(3000.0)
    row = next(item for item in audit if item["event_id"] == EVENT_2019.event_id)
    assert row["applied"] is False
    assert row["reason"] == "NO_LISTING_QUOTE_AVAILABLE_AS_OF_SIGNAL_END"


def test_listing_only_policy_requires_raw_quote_after_listing_date():
    with pytest.raises(ValueError, match="MISSING_RAW_DEBENTURE_LISTING_CLOSE"):
        adjust_signal_price_maps(
            date(2019, 11, 29),
            {"BRITANNIA": point("2018-11-30", 3000.0)},
            {"BRITANNIA": point("2019-11-29", 2700.0)},
            policy="listing_only",
            parent_ex_date_closes={EVENT_2019.event_id: 2800.0},
            listing_debenture_closes={},
        )


def test_listing_only_uses_observed_listing_quote_after_it_is_available():
    start, end, audit = adjust_signal_price_maps(
        date(2019, 11, 29),
        {"BRITANNIA": point("2018-11-30", 3000.0)},
        {"BRITANNIA": point("2019-11-29", 2700.0)},
        policy="listing_only",
        parent_ex_date_closes={EVENT_2019.event_id: 2800.0},
        listing_debenture_closes={EVENT_2019.event_id: 27.5},
    )

    factor = 2800.0 / (2800.0 + 27.5)
    assert start["BRITANNIA"].close == pytest.approx(3000.0 * factor)
    assert end["BRITANNIA"].close == pytest.approx(2700.0)
    row = next(item for item in audit if item["event_id"] == EVENT_2019.event_id)
    assert row["distribution_value_source"] == "RAW_DEBENTURE_FIRST_LISTING_CLOSE"


def test_adjustment_fails_closed_without_parent_ex_date_close():
    with pytest.raises(ValueError, match="MISSING_RAW_PARENT_EX_DATE_CLOSE"):
        adjust_signal_price_maps(
            date(2019, 8, 30),
            {"BRITANNIA": point("2018-08-31", 3000.0)},
            {"BRITANNIA": point("2019-08-30", 2900.0)},
            policy="provisional_face_value",
            parent_ex_date_closes={},
        )


def test_raw_non_equity_close_can_be_loaded_by_isin(tmp_path):
    path = tmp_path / "nse.csv"
    path.write_text(
        "SYMBOL,SERIES,ISIN,OPEN,HIGH,LOW,CLOSE,TIMESTAMP\n"
        "BRITANNIA,N1,INE216A07052,27,28,26,27.5,09-Oct-2019\n",
        encoding="utf-8",
    )

    value = load_raw_instrument_close_by_isin(
        path, "INE216A07052", date(2019, 10, 9)
    )
    assert value == pytest.approx(27.5)


def test_raw_instrument_close_lookup_requires_exactly_one_matching_isin_row(tmp_path):
    path = tmp_path / "nse.csv"
    path.write_text(
        "SYMBOL,SERIES,ISIN,OPEN,HIGH,LOW,CLOSE,TIMESTAMP\n"
        "BRITANNIA,N1,INE216A07052,27,28,26,27.5,09-Oct-2019\n"
        "BRITANNIA,N1,INE216A07052,27,28,26,27.6,09-Oct-2019\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected exactly one raw close"):
        load_raw_instrument_close_by_isin(
            path, "INE216A07052", date(2019, 10, 9)
        )



def test_selection_adjuster_does_not_change_raw_execution_open():
    from strategy.momentum import Member
    from strategy.selection import build_quarterly_selection_audit

    dates = [
        date(2020, 5, 29),
        date(2021, 5, 31),
        date(2021, 6, 30),
        date(2021, 7, 1),
    ]

    class FakePriceStore:
        def __init__(self):
            self.execution_open = 100.0

        def prices(self, trading_date):
            if trading_date == date(2020, 5, 29):
                return {"BRITANNIA": point("2020-05-29", 100.0)}
            if trading_date == date(2021, 5, 31):
                return {"BRITANNIA": point("2021-05-31", 90.0)}
            if trading_date == date(2021, 7, 1):
                return {
                    "BRITANNIA": SimpleNamespace(
                        date=date(2021, 7, 1),
                        close=101.0,
                        open=self.execution_open,
                    )
                }
            raise AssertionError(f"unexpected price request: {trading_date}")

    store = FakePriceStore()

    def adjuster(formation_end, start_prices, end_prices):
        return (
            {"BRITANNIA": point("2020-05-29", 95.0)},
            end_prices,
        )

    result = build_quarterly_selection_audit(
        trading_dates=dates,
        price_store=store,
        baseline=[Member("BRITANNIA", "Britannia Industries", "INE216A07052")],
        transitions=[],
        identity_events=[],
        start=date(2021, 6, 30),
        end=date(2021, 6, 30),
        holdings=1,
        decision_dates=[date(2021, 6, 30)],
        signal_price_adjuster=adjuster,
    )

    assert result[0].selected_symbols == ("BRITANNIA",)
    assert result[0].missing_execution_opens == ()
    assert store.execution_open == pytest.approx(100.0)



def test_audit_csv_writer_accepts_heterogeneous_event_rows(tmp_path):
    import csv
    from audit.phase1b_britannia_signal_adjustment_audit import write_csv

    output = tmp_path / "events.csv"
    write_csv(output, [
        {"event_id": "event-a", "applied": False, "reason": "NOT_YET_OCCURRED"},
        {
            "event_id": "event-b",
            "applied": True,
            "reason": "ADJUSTED",
            "factor_applied_to_pre_event_equity_prices": 0.99,
        },
    ])

    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["event_id"] == "event-a"
    assert rows[0]["factor_applied_to_pre_event_equity_prices"] == ""
    assert rows[1]["factor_applied_to_pre_event_equity_prices"] == "0.99"
