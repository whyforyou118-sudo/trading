"""Synthetic tests for ledger corporate-action and rights mechanics.

These tests validate accounting primitives only. They do not claim that historical
NSE corporate-action records have been fully ingested or independently verified.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio.accounting import (
    PortfolioState,
    SecurityConversion,
    ShareRatioAction,
    apply_ledger,
)
from portfolio.rights import RightsEntitlement


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
