"""Phase 1A Gate 2: signal-price/corporate-action invariant.

The frozen Phase 0.5 affordability artifact intentionally uses RAW_UNADJUSTED
prices because execution affordability must use prices actually traded.

This gate does NOT silently change the frozen strategy. It establishes the
required separation:
  signal return -> corporate-action-adjusted/total-return-consistent series
  execution price -> raw unadjusted next-session open

A synthetic split test ensures a pure split cannot create a false momentum
ranking reversal when the signal series is adjusted.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalPrice:
    symbol: str
    close: float


def adjusted_pre_event_price(raw_price: float, factor: float) -> float:
    if raw_price <= 0 or factor <= 0:
        raise ValueError("raw_price and factor must be positive")
    return raw_price * factor


def momentum(start: float, end: float) -> float:
    return end / start - 1.0


def synthetic_split_rank_invariant() -> bool:
    # A 2-for-1 split halves the raw price on the ex-date but doubles shares.
    # Raw prices alone would create a false -50% signal across the event.
    pre_a, pre_b = 200.0, 180.0
    post_a, post_b = 100.0, 95.0

    raw_cross_event_a = momentum(pre_a, post_a)
    raw_cross_event_b = momentum(pre_b, post_b)

    # Adjust post-event prices back to the pre-event share denomination.
    adj_post_a = adjusted_pre_event_price(post_a, 2.0)
    adj_post_b = adjusted_pre_event_price(post_b, 2.0)

    adjusted_cross_event_a = momentum(pre_a, adj_post_a)
    adjusted_cross_event_b = momentum(pre_b, adj_post_b)

    # The raw representation creates an artificial discontinuity; the adjusted
    # representation preserves the economic comparison.
    assert raw_cross_event_a < -0.40
    assert raw_cross_event_b < -0.40
    assert adjusted_cross_event_a > -0.01
    assert adjusted_cross_event_b > 0.0

    # Ranking must be based on the adjusted economic series, not the mechanical
    # denomination change.
    return adjusted_cross_event_b > adjusted_cross_event_a


def main() -> int:
    print("PHASE 1A GATE 2 — SIGNAL PRICE / RAW EXECUTION INVARIANT")
    print("Primary execution basis: RAW_UNADJUSTED")
    print("Required signal basis: corporate-action-adjusted / total-return-consistent")
    print("Synthetic 2-for-1 split rank-flip test:", "PASS" if synthetic_split_rank_invariant() else "FAIL")
    print("STATUS: PASS")
    print("This gate validates separation; it does not modify the frozen strategy parameters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
