"""Point-in-time corporate-action adjustment for momentum signal prices.

Execution prices remain raw and are never modified by this module. The primary
Britannia policy uses the approved provisional face-value mark for each
debenture distribution. A listing-only sensitivity uses the observed raw
debenture close only after the first tradable date; it does not backfill a
future listing quote into an earlier signal date.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping


@dataclass(frozen=True)
class SignalDistributionEvent:
    event_id: str
    symbol: str
    ex_date: date
    first_tradable_date: date
    isin: str
    face_value: float


@dataclass(frozen=True)
class SignalPricePoint:
    date: date
    close: float


BRITANNIA_DEBENTURE_EVENTS = (
    SignalDistributionEvent(
        event_id="BRITANNIA_2019_BONUS_DEBENTURE",
        symbol="BRITANNIA",
        ex_date=date(2019, 8, 22),
        first_tradable_date=date(2019, 10, 9),
        isin="INE216A07052",
        face_value=30.0,
    ),
    SignalDistributionEvent(
        event_id="BRITANNIA_2021_BONUS_DEBENTURE",
        symbol="BRITANNIA",
        ex_date=date(2021, 5, 25),
        first_tradable_date=date(2021, 7, 20),
        isin="INE216A08027",
        face_value=29.0,
    ),
)


def adjust_signal_price_maps(
    formation_end: date,
    start_prices: Mapping[str, object],
    end_prices: Mapping[str, object],
    *,
    policy: str,
    parent_ex_date_closes: Mapping[str, float],
    listing_debenture_closes: Mapping[str, float] | None = None,
) -> tuple[dict[str, SignalPricePoint], dict[str, SignalPricePoint], list[dict[str, object]]]:
    """Return adjusted signal maps and a per-event audit trail.

    The event value is added to the ex-date equity close to form the total-value
    denominator. The pre-event equity-price adjustment factor is
    P_ex / (P_ex + distribution_value), which avoids counting a mechanical
    distribution-related price drop as negative momentum.

    The primary policy is provisional_face_value. The listing_only sensitivity
    does not adjust before the instrument's first tradable date; on/after that
    date, its observed raw listing close is required.
    """
    if policy not in {"provisional_face_value", "listing_only"}:
        raise ValueError(f"unsupported signal adjustment policy: {policy}")
    listing_debenture_closes = listing_debenture_closes or {}

    def copy_points(prices: Mapping[str, object]) -> dict[str, SignalPricePoint]:
        result: dict[str, SignalPricePoint] = {}
        for symbol, point in prices.items():
            try:
                point_date = getattr(point, "date")
                close = float(getattr(point, "close"))
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError(f"signal price missing date/close for {symbol}") from exc
            if not isinstance(point_date, date):
                raise ValueError(f"signal price date is not a date for {symbol}")
            if close <= 0:
                raise ValueError(f"signal price close must be positive for {symbol}")
            result[symbol] = SignalPricePoint(point_date, close)
        return result

    adjusted_start = copy_points(start_prices)
    adjusted_end = copy_points(end_prices)
    audit: list[dict[str, object]] = []

    for event in BRITANNIA_DEBENTURE_EVENTS:
        base = {
            "event_id": event.event_id,
            "symbol": event.symbol,
            "ex_date": event.ex_date.isoformat(),
            "first_tradable_date": event.first_tradable_date.isoformat(),
            "formation_end": formation_end.isoformat(),
            "policy": policy,
        }
        if formation_end < event.ex_date:
            audit.append({**base, "applied": False, "reason": "EVENT_NOT_YET_OCCURRED"})
            continue
        if policy == "listing_only" and formation_end < event.first_tradable_date:
            audit.append({
                **base,
                "applied": False,
                "reason": "NO_LISTING_QUOTE_AVAILABLE_AS_OF_SIGNAL_END",
            })
            continue

        parent_close = parent_ex_date_closes.get(event.event_id)
        if parent_close is None or float(parent_close) <= 0:
            raise ValueError(f"MISSING_RAW_PARENT_EX_DATE_CLOSE:{event.event_id}")
        if policy == "provisional_face_value":
            distribution_value = event.face_value
            value_source = "PROVISIONAL_FACE_VALUE"
        else:
            listing_close = listing_debenture_closes.get(event.event_id)
            if listing_close is None or float(listing_close) <= 0:
                raise ValueError(f"MISSING_RAW_DEBENTURE_LISTING_CLOSE:{event.event_id}")
            distribution_value = float(listing_close)
            value_source = "RAW_DEBENTURE_FIRST_LISTING_CLOSE"

        factor = float(parent_close) / (float(parent_close) + distribution_value)
        if not 0 < factor < 1:
            raise ValueError(f"INVALID_CORPORATE_ACTION_FACTOR:{event.event_id}")

        for points in (adjusted_start, adjusted_end):
            point = points.get(event.symbol)
            if point is not None and point.date < event.ex_date:
                points[event.symbol] = SignalPricePoint(point.date, point.close * factor)

        audit.append({
            **base,
            "applied": True,
            "reason": "PRE_EVENT_EQUITY_SIGNAL_PRICE_BACK_ADJUSTED",
            "parent_raw_close_on_ex_date": float(parent_close),
            "distribution_value_per_parent_share": distribution_value,
            "distribution_value_source": value_source,
            "factor_applied_to_pre_event_equity_prices": factor,
        })

    return adjusted_start, adjusted_end, audit
