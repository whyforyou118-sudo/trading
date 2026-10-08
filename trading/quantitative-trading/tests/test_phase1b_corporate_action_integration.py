"""Synthetic tests for ledger corporate-action and rights mechanics.

These tests validate accounting primitives and rights-policy mechanics only.
They do not claim that historical corporate-action records have all been
independently verified or that the full historical simulation is ready.
"""
from datetime import date
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio.accounting import (
    PortfolioState,
    SecurityConversion,
    ShareRatioAction,
    apply_ledger,
)
from portfolio.costs import DeliveryCostModel
from portfolio.rights import RightsEntitlement, RightsRenunciation


def test_share_ratio_action_changes_shares_without_changing_cash():
    state = apply_ledger(
        initial_cash=1_234.50,
        events=[ShareRatioAction(
            date="2024-01-05", symbol="AAA", numerator=10, denominator=1
        )],
        initial_positions={"AAA": 7},
    )

    assert state.positions == {"AAA": 70}
    assert state.cash == pytest.approx(1_234.50)


def test_security_conversion_merges_into_existing_new_security_position():
    state = apply_ledger(
        initial_cash=5_000.0,
        events=[SecurityConversion(
            date="2024-04-01",
            old_symbol="OLD",
            new_symbol="NEW",
            numerator=42,
            denominator=25,
        )],
        initial_positions={"OLD": 25, "NEW": 3},
    )

    assert state.positions == {"NEW": 45}
    assert state.cash == pytest.approx(5_000.0)


def test_non_integral_share_ratio_action_fails_closed():
    with pytest.raises(ValueError, match="non-integral share result"):
        apply_ledger(
            initial_cash=1_000.0,
            events=[ShareRatioAction(
                date="2024-01-05", symbol="AAA", numerator=3, denominator=2
            )],
            initial_positions={"AAA": 1},
        )


def test_rights_entitlement_uses_parent_shares_and_ignores_fractional_entitlement():
    event = RightsEntitlement(
        date="2024-01-10",
        parent_symbol="PARENT",
        re_symbol="PARENT-RE",
        numerator=6,
        denominator=179,
    )
    state = apply_ledger(
        initial_cash=2_000.0,
        events=[event],
        initial_positions={"PARENT": 100},
    )

    assert state.positions == {"PARENT": 100, "PARENT-RE": 3}
    assert state.cash == pytest.approx(2_000.0)


def test_rights_are_sold_at_first_tradable_raw_open_with_costs():
    entitlement = RightsEntitlement(
        date="2024-01-10",
        parent_symbol="GRASIM",
        re_symbol="GRASIM-RE",
        numerator=6,
        denominator=179,
    )
    renunciation = RightsRenunciation(
        entitlement=entitlement,
        first_tradable_date="2024-01-17",
        first_tradable_open=320.05,
    )
    costs_model = DeliveryCostModel.from_csv(
        ROOT / "data" / "reference" / "zerodha_delivery_cost_schedule.csv"
    )
    trade = renunciation.build_trade(parent_shares=100, cost_model=costs_model)

    assert trade is not None
    assert trade.date == "2024-01-17"
    assert trade.symbol == "GRASIM-RE"
    assert trade.side == "SELL"
    assert trade.shares == 3
    assert trade.price == pytest.approx(320.05)  # raw open; slippage is a cost
    assert trade.costs.slippage == pytest.approx(3 * 320.05 * 0.001)

    state = apply_ledger(
        initial_cash=2_000.0,
        events=[entitlement, trade],
        initial_positions={"GRASIM": 100},
    )
    assert state.positions == {"GRASIM": 100}
    assert state.cash == pytest.approx(2_000.0 + 3 * 320.05 - trade.costs.total)
    assert state.cumulative_costs.total == pytest.approx(trade.costs.total)


def test_zero_rights_entitlement_creates_no_sale():
    entitlement = RightsEntitlement(
        date="2024-07-26",
        parent_symbol="TATACONSUM",
        re_symbol="TATACON-RE",
        numerator=1,
        denominator=26,
    )
    renunciation = RightsRenunciation(
        entitlement=entitlement,
        first_tradable_date="2024-08-05",
        first_tradable_open=303.0,
    )
    costs_model = DeliveryCostModel.from_csv(
        ROOT / "data" / "reference" / "zerodha_delivery_cost_schedule.csv"
    )

    assert renunciation.build_trade(parent_shares=25, cost_model=costs_model) is None


def test_rights_sale_must_be_after_entitlement_date():
    entitlement = RightsEntitlement(
        date="2024-01-10",
        parent_symbol="GRASIM",
        re_symbol="GRASIM-RE",
        numerator=6,
        denominator=179,
    )
    with pytest.raises(ValueError, match="must follow"):
        RightsRenunciation(
            entitlement=entitlement,
            first_tradable_date="2024-01-10",
            first_tradable_open=320.05,
        )
