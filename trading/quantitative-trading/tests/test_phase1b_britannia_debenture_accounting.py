"""Britannia bonus-debenture ledger tests.

Synthetic tests for the explicitly versioned face-value convention. These tests
validate event mechanics, not the complete historical event dataset or Run 1.
"""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from portfolio.accounting import (
    DebentureCoupon,
    DebentureEntitlement,
    DebentureRedemption,
    Dividend,
    Trade,
    apply_ledger,
    debenture_mark_price,
)


def entitlement(event_id="BRIT-2019-ENTITLEMENT"):
    return DebentureEntitlement(
        event_id=event_id,
        date="2019-08-22",
        parent_symbol="BRITANNIA",
        debenture_symbol="BRIT-DEB-2019",
        numerator=1,
        denominator=1,
        face_value=30.0,
        coupon_rate=0.08,
        source_ref="https://nsearchives.nseindia.com/corporate/BRITANNIA_28082019165059_OUTCOMEBONUSDEBENTURECOMMITTEEALLOTMENT_260.pdf",
    )


def test_entitlement_creates_separate_debt_position_at_ex_date():
    state = apply_ledger(
        initial_cash=1_000.0,
        events=[entitlement()],
        initial_positions={"BRITANNIA": 12},
    )

    assert state.shares("BRITANNIA") == 12
    assert state.shares("BRIT-DEB-2019") == 12
    assert state.cash == pytest.approx(1_000.0)
    # The caller must explicitly supply the provisional face-value mark before listing.
    assert state.market_value({"BRITANNIA": 500.0, "BRIT-DEB-2019": 30.0}) == pytest.approx(7_360.0)


def test_ex_date_entitlement_uses_pre_open_parent_holding_not_same_day_purchase():
    state = apply_ledger(
        initial_cash=10_000.0,
        events=[
            entitlement(),
            Trade("2019-08-22", "BRITANNIA", "BUY", 10, 300.0),
        ],
        initial_positions={"BRITANNIA": 4},
    )

    assert state.shares("BRIT-DEB-2019") == 4
    assert state.shares("BRITANNIA") == 14


def test_coupon_is_credited_once_from_explicit_per_unit_amount():
    state = apply_ledger(
        initial_cash=100.0,
        events=[
            entitlement(),
            DebentureCoupon(
                event_id="BRIT-2019-COUPON-Y1",
                date="2020-08-28",
                debenture_symbol="BRIT-DEB-2019",
                per_debenture_amount=2.40,
                source_ref="https://nsearchives.nseindia.com/corporates/offerdocument/scheme/IM_BRITANNIA.pdf",
            ),
        ],
        initial_positions={"BRITANNIA": 5},
    )

    assert state.cash == pytest.approx(112.0)
    assert state.shares("BRIT-DEB-2019") == 5


def test_redemption_credits_principal_and_final_coupon_and_removes_position():
    state = apply_ledger(
        initial_cash=50.0,
        events=[
            entitlement(),
            DebentureRedemption(
                event_id="BRIT-2019-REDEMPTION",
                date="2022-08-26",
                debenture_symbol="BRIT-DEB-2019",
                principal_per_debenture=30.0,
                final_coupon_per_debenture=2.40,
                source_ref="https://nsearchives.nseindia.com/corporate/BRITANNIA_04112022214406_Outcome_Signed.pdf",
            ),
        ],
        initial_positions={"BRITANNIA": 3},
    )

    assert state.cash == pytest.approx(147.20)
    assert state.shares("BRIT-DEB-2019") == 0
    assert "BRIT-DEB-2019" not in state.positions
    assert state.shares("BRITANNIA") == 3


def test_duplicate_debenture_cashflow_event_id_fails_closed():
    coupon = DebentureCoupon(
        event_id="DUPLICATE-COUPON",
        date="2020-08-28",
        debenture_symbol="BRIT-DEB-2019",
        per_debenture_amount=2.40,
        source_ref="issuer coupon schedule",
    )
    with pytest.raises(ValueError, match="duplicate ledger event_id"):
        apply_ledger(
            initial_cash=0.0,
            events=[entitlement(), coupon, coupon],
            initial_positions={"BRITANNIA": 2},
        )


def test_coupon_without_outstanding_debentures_fails_closed():
    with pytest.raises(ValueError, match="no outstanding debentures"):
        apply_ledger(
            initial_cash=0.0,
            events=[
                DebentureCoupon(
                    event_id="ORPHAN-COUPON",
                    date="2020-08-28",
                    debenture_symbol="BRIT-DEB-2019",
                    per_debenture_amount=2.40,
                    source_ref="issuer coupon schedule",
                )
            ],
        )



def test_face_value_mark_prelisting_does_not_use_future_listing_quote():
    assert debenture_mark_price(
        valuation_date="2019-09-30",
        first_tradable_date="2019-10-09",
        face_value=30.0,
        raw_market_price=30.81,
    ) == pytest.approx(30.0)


def test_raw_market_price_is_required_on_and_after_listing():
    assert debenture_mark_price(
        valuation_date="2019-10-09",
        first_tradable_date="2019-10-09",
        face_value=30.0,
        raw_market_price=30.81,
    ) == pytest.approx(30.81)
    with pytest.raises(ValueError, match="MISSING_RAW_DEBENTURE_MARK"):
        debenture_mark_price(
            valuation_date="2019-10-10",
            first_tradable_date="2019-10-09",
            face_value=30.0,
            raw_market_price=None,
        )
