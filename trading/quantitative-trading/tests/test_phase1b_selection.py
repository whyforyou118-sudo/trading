from datetime import date
from types import SimpleNamespace

import pytest

from strategy.momentum import Member
from strategy.selection import build_quarterly_selection_audit


class FakeStore:
    def __init__(self, values):
        self.values = values

    def prices(self, trading_date):
        return self.values[trading_date]


def test_quarterly_selection_uses_12m_formation_and_one_month_skip():
    dates = [
        date(2023, 1, 31), date(2023, 2, 28), date(2023, 3, 31),
        date(2023, 4, 3),
    ]
    store = FakeStore({
        date(2023, 1, 31): {"AAA": SimpleNamespace(close=100), "BBB": SimpleNamespace(close=100)},
        date(2023, 2, 28): {"AAA": SimpleNamespace(close=120), "BBB": SimpleNamespace(close=110)},
        date(2023, 3, 31): {"AAA": SimpleNamespace(open=125), "BBB": SimpleNamespace(open=115)},
        date(2023, 4, 3): {"AAA": SimpleNamespace(open=126), "BBB": SimpleNamespace(open=116)},
    })
    # Decision date must have 12 months of history; use the exact date as a
    # small direct contract check for the date helpers in the next test.
    with pytest.raises(ValueError, match="insufficient formation history"):
        build_quarterly_selection_audit(
            trading_dates=dates,
            price_store=store,
            baseline=[Member("AAA", "A", "ISIN-A")],
            transitions=[],
            identity_events=[],
            start=date(2023, 1, 1),
            end=date(2023, 3, 31),
            holdings=1,
        )


def test_tie_break_and_missing_execution_open_block_without_replacement():
    # A 14-month calendar window provides a valid 12M/1M signal for March 2024.
    dates = []
    cursor = date(2023, 1, 31)
    from calendar import monthrange
    for year in (2023, 2024):
        for month in range(1, 13):
            dates.append(date(year, month, monthrange(year, month)[1]))
    dates = [d for d in dates if d >= date(2023, 1, 1)]
    dates.append(date(2024, 4, 1))
    dates = sorted(set(dates))
    start_date = date(2023, 2, 28)
    end_date = date(2024, 2, 29)
    decision = date(2024, 3, 31)
    execution = date(2024, 4, 1)
    store = FakeStore({
        start_date: {
            "AAA": SimpleNamespace(close=100),
            "BBB": SimpleNamespace(close=100),
            "CCC": SimpleNamespace(close=100),
        },
        end_date: {
            "AAA": SimpleNamespace(close=120),
            "BBB": SimpleNamespace(close=120),
            "CCC": SimpleNamespace(close=110),
        },
        execution: {
            "BBB": SimpleNamespace(open=50),
            "CCC": SimpleNamespace(open=40),
        },
    })
    rows = build_quarterly_selection_audit(
        trading_dates=dates,
        price_store=store,
        baseline=[
            Member("BBB", "B", "ISIN-B"),
            Member("AAA", "A", "ISIN-A"),
            Member("CCC", "C", "ISIN-C"),
        ],
        transitions=[],
        identity_events=[],
        start=decision,
        end=decision,
        holdings=2,
    )
    assert len(rows) == 1
    row = rows[0]
    assert row.decision_date == decision
    assert row.formation_start == start_date
    assert row.formation_end == end_date
    assert row.execution_date == execution
    assert row.selected_symbols == ("AAA", "BBB")
    assert row.missing_execution_opens == ("AAA",)
    assert row.status == "BLOCKED"
    assert row.reason == "MISSING_EXECUTION_OPEN:AAA"


def test_missing_signal_prices_exclude_name_from_ranking():
    dates = []
    from calendar import monthrange
    for year in (2023, 2024):
        for month in range(1, 13):
            dates.append(date(year, month, monthrange(year, month)[1]))
    dates.append(date(2024, 4, 1))
    start_date = date(2023, 2, 28)
    end_date = date(2024, 2, 29)
    execution = date(2024, 4, 1)
    store = FakeStore({
        start_date: {"AAA": SimpleNamespace(close=100), "BBB": SimpleNamespace(close=100)},
        end_date: {"AAA": SimpleNamespace(close=130)},
        execution: {"AAA": SimpleNamespace(open=140)},
    })
    rows = build_quarterly_selection_audit(
        trading_dates=dates,
        price_store=store,
        baseline=[
            Member("AAA", "A", "ISIN-A"),
            Member("BBB", "B", "ISIN-B"),
        ],
        transitions=[],
        identity_events=[],
        start=date(2024, 3, 31),
        end=date(2024, 3, 31),
        holdings=1,
    )
    assert rows[0].signal_eligible_count == 1
    assert rows[0].selected_symbols == ("AAA",)
    assert rows[0].status == "PASS"
