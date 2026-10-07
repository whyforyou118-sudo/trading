"""Phase 1A Gate 3: real corporate-action and dividend ledger replays.

Uses real events represented in the repository's NSE corporate-action sample:
- GAIL 1:3 bonus, ex-date 2018-03-27
- GAIL dividend, ex-date 2018-01-18
- HDFC -> HDFC Bank amalgamation, effective 2023-07-01
- TCS dividend, ex-date 2018-01-22

This gate is deliberately a deterministic replay gate, not a performance run.
Dividend cash is credited on the declared ex/entitlement date in this replay;
the record/payment dates are retained as evidence metadata. A production
ingestion layer must preserve those dates explicitly rather than infer them.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from portfolio.accounting import (
    Dividend,
    PortfolioState,
    ShareRatioAction,
    Trade,
    apply_ledger,
)


@dataclass(frozen=True)
class SecurityConversion:
    date: str
    source: str
    target: str
    numerator: int
    denominator: int

    def apply(self, state: PortfolioState) -> None:
        old = state.shares(self.source)
        if old * self.numerator % self.denominator:
            raise ValueError("non-integral merger conversion")
        new = old * self.numerator // self.denominator
        state.positions.pop(self.source, None)
        if new:
            state.positions[self.target] = state.shares(self.target) + new


def replay_gail_bonus() -> None:
    # Real event: GAIL Bonus 1:3, ex-date 2018-03-27.
    events = [
        Trade("2018-03-26", "GAIL", "BUY", 30, 500.0),
        ShareRatioAction("2018-03-27", "GAIL", 4, 3),
    ]
    state = apply_ledger(0.0, events)
    assert state.shares("GAIL") == 40


def replay_real_dividend() -> None:
    # Real NSE sample: GAIL interim dividend Rs 7.65/share,
    # ex-date 2018-01-18, record date 2018-01-20.
    events = [
        Trade("2018-01-17", "GAIL", "BUY", 100, 500.0),
        Dividend("2018-01-18", "GAIL", 7.65),
        Trade("2018-01-19", "GAIL", "SELL", 100, 500.0),
    ]
    state = apply_ledger(0.0, events)
    assert isclose(state.cumulative_dividends, 765.0)
    assert isclose(state.cash, 765.0)


def replay_real_tcs_dividend() -> None:
    # Real NSE sample: TCS interim dividend Rs 7/share,
    # ex-date 2018-01-22, record date 2018-01-23.
    events = [
        Trade("2018-01-19", "TCS", "BUY", 10, 3000.0),
        Dividend("2018-01-22", "TCS", 7.0),
    ]
    state = apply_ledger(0.0, events)
    assert isclose(state.cumulative_dividends, 70.0)


def replay_hdfc_merger() -> None:
    # Real scheme: 42 HDFC Bank shares for every 25 HDFC shares.
    # Effective date: 2023-07-01. HDFC is extinguished.
    state = PortfolioState(cash=0.0, positions={"HDFC": 25})
    conversion = SecurityConversion(
        "2023-07-01", "HDFC", "HDFCBANK", 42, 25
    )
    conversion.apply(state)
    assert state.shares("HDFC") == 0
    assert state.shares("HDFCBANK") == 42


def main() -> int:
    replay_gail_bonus()
    replay_real_dividend()
    replay_real_tcs_dividend()
    replay_hdfc_merger()
    print("PHASE 1A GATE 3 — REAL CORPORATE-ACTION / DIVIDEND LEDGER REPLAYS")
    print("GAIL bonus 1:3 replay: PASS")
    print("GAIL dividend replay: PASS")
    print("TCS dividend replay: PASS")
    print("HDFC -> HDFCBANK merger conversion replay: PASS")
    print("STATUS: PASS")
    print("No performance calculation or strategy parameter change was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
