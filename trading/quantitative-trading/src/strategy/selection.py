"""Chronological quarterly signal audit for the frozen V6 selection rules.

This module produces signal/ranking evidence only. It does not execute trades,
apply dividends/corporate actions, or calculate portfolio returns.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Callable, Iterable, Mapping, Protocol, Sequence

from strategy.momentum import (
    Member,
    formation_and_skip_dates,
    month_ends,
    next_trading_day,
    pit_membership,
    quarterly_decision_dates,
    rank_candidates,
)


class PriceStore(Protocol):
    def prices(self, trading_date: date) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class QuarterlySelection:
    decision_date: date
    formation_start: date
    formation_end: date
    execution_date: date
    member_count: int
    signal_eligible_count: int
    ranked_candidates: tuple[tuple[str, float, int], ...]
    selected_symbols: tuple[str, ...]
    missing_execution_opens: tuple[str, ...]
    status: str
    reason: str


def build_quarterly_selection_audit(
    *,
    trading_dates: Sequence[date],
    price_store: PriceStore,
    baseline: Iterable[Member],
    transitions: Iterable[dict[str, str]],
    identity_events: Iterable[dict[str, str]],
    start: date = date(2018, 1, 1),
    end: date = date(2025, 12, 31),
    formation_months: int = 12,
    skip_months: int = 1,
    holdings: int = 5,
    decision_dates: Sequence[date] | None = None,
    signal_price_adjuster: Callable[[date, Mapping[str, object], Mapping[str, object]], tuple[Mapping[str, object], Mapping[str, object]]] | None = None,
) -> list[QuarterlySelection]:
    """Build deterministic signal/ranking rows without computing performance.

    Signal inputs are month-end raw close prices. Ranking is descending
    momentum with symbol-ascending tie breaks. The selected Top-N is fixed
    before execution-open availability is checked: a missing selected open
    blocks that rebalance rather than silently replacing the name.
    """
    dates = sorted(set(trading_dates))
    if not dates:
        raise ValueError("trading_dates cannot be empty")
    if holdings <= 0:
        raise ValueError("holdings must be positive")
    if start > end:
        raise ValueError("start must not be after end")

    ends = month_ends(dates)
    if decision_dates is None:
        decisions = quarterly_decision_dates(dates, start, end)
    else:
        calendar_dates = set(dates)
        decisions = sorted(set(decision_dates))
        invalid_dates = [
            d for d in decisions
            if d not in calendar_dates
            or not start <= d <= end
            or d.month not in (3, 6, 9, 12)
        ]
        if invalid_dates:
            raise ValueError(
                "explicit decision_dates contain dates outside the quarterly "
                f"trading calendar or requested interval: {invalid_dates}"
            )
    if not decisions:
        raise ValueError("no quarterly decision dates in requested interval")

    baseline_rows = tuple(baseline)
    transition_rows = tuple(transitions)
    identity_rows = tuple(identity_events)
    out: list[QuarterlySelection] = []

    for decision in decisions:
        formation_start, formation_end = formation_and_skip_dates(
            decision, ends, formation_months, skip_months
        )
        execution_date = next_trading_day(dates, decision)
        members = pit_membership(
            baseline_rows, transition_rows, identity_rows, decision
        )
        start_prices = price_store.prices(formation_start)
        end_prices = price_store.prices(formation_end)
        execution_prices = price_store.prices(execution_date)

        # Ask for all scoreable names so the audit retains the full eligible
        # candidate count/ranks, not merely the selected Top-N.
        scored = rank_candidates(
            members,
            start_prices,
            end_prices,
            holdings=max(len(members), holdings),
        )
        selected = tuple(scored[:holdings])
        missing = tuple(
            symbol
            for symbol, _, _ in selected
            if symbol not in execution_prices
            or not isfinite(float(getattr(execution_prices[symbol], "open", 0.0)))
            or float(getattr(execution_prices[symbol], "open", 0.0)) <= 0
        )
        if missing:
            status = "BLOCKED"
            reason = "MISSING_EXECUTION_OPEN:" + ",".join(missing)
        elif not scored:
            status = "BLOCKED"
            reason = "NO_SIGNAL_ELIGIBLE_CANDIDATES"
        elif len(selected) < holdings:
            status = "PASS_FEWER_THAN_TARGET_HOLDINGS"
            reason = "INSUFFICIENT_SIGNAL_ELIGIBLE_NAMES; retain unallocated target capital as cash"
        else:
            status = "PASS"
            reason = "TOP_N_RANKING_AND_EXECUTION_OPEN_AVAILABLE"

        out.append(QuarterlySelection(
            decision_date=decision,
            formation_start=formation_start,
            formation_end=formation_end,
            execution_date=execution_date,
            member_count=len(members),
            signal_eligible_count=len(scored),
            ranked_candidates=tuple(scored),
            selected_symbols=tuple(symbol for symbol, _, _ in selected),
            missing_execution_opens=missing,
            status=status,
            reason=reason,
        ))
    return out
