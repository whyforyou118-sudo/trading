"""PIT NIFTY-50 momentum selection for the frozen V6 contract.

No portfolio accounting is performed here. The module only resolves decision
and execution dates, reconstructs PIT membership, calculates the registered
12M/1M momentum signal, and ranks candidates deterministically.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Member:
    symbol: str
    company_name: str
    isin: str


def month_ends(trading_dates: Sequence[date]) -> Mapping[tuple[int, int], date]:
    out: dict[tuple[int, int], date] = {}
    for d in sorted(trading_dates):
        out[(d.year, d.month)] = d
    return out


def pit_membership(
    baseline: Iterable[Member],
    transitions: Iterable[dict[str, str]],
    identity_events: Iterable[dict[str, str]],
    through: date,
) -> dict[str, Member]:
    state = {m.symbol: m for m in baseline}
    events = sorted(
        [*transitions, *identity_events],
        key=lambda r: (r.get("effective_date", r.get("event_date", "")), r.get("symbol", "")),
    )
    for row in events:
        d = date.fromisoformat(row.get("effective_date", row.get("event_date", "")))
        if d > through:
            break
        if "action" in row:
            if row["action"] == "INCLUSION":
                state[row["symbol"]] = Member(row["symbol"], row["company_name"], row["isin"])
            elif row["action"] == "EXCLUSION":
                state.pop(row["symbol"], None)
        elif row.get("apply_to_membership_state", "").lower() == "true":
            old = row.get("old_isin", "")
            if row["symbol"] in state and state[row["symbol"]].isin == old:
                m = state[row["symbol"]]
                state[row["symbol"]] = Member(m.symbol, m.company_name, row["new_isin"])
    return state


def quarterly_decision_dates(trading_dates: Sequence[date], start: date, end: date) -> list[date]:
    selected: dict[tuple[int, int], date] = {}
    for d in sorted(trading_dates):
        if start <= d <= end and d.month in (3, 6, 9, 12):
            selected[(d.year, d.month)] = d
    return list(selected.values())


def next_trading_day(trading_dates: Sequence[date], after: date) -> date:
    for d in sorted(trading_dates):
        if d > after:
            return d
    raise ValueError(f"no trading day after {after}")


def formation_and_skip_dates(
    decision: date,
    ends: Mapping[tuple[int, int], date],
    formation_months: int = 12,
    skip_months: int = 1,
) -> tuple[date, date]:
    if formation_months <= 0 or skip_months < 0:
        raise ValueError("formation_months must be positive and skip_months non-negative")
    # The frozen 12M/1M convention: signal uses the month-end one month before
    # decision, versus the month-end 13 months before decision.
    end_index = decision.year * 12 + decision.month - 1 - skip_months
    start_index = end_index - formation_months
    end_key = (end_index // 12, end_index % 12 + 1)
    start_key = (start_index // 12, start_index % 12 + 1)
    try:
        return ends[start_key], ends[end_key]
    except KeyError as exc:
        raise ValueError(f"insufficient formation history for {decision}") from exc


def rank_candidates(
    members: Mapping[str, Member],
    start_prices: Mapping[str, object],
    end_prices: Mapping[str, object],
    holdings: int = 5,
) -> list[tuple[str, float, int]]:
    scored: list[tuple[str, float]] = []
    for symbol in members:
        if symbol not in start_prices or symbol not in end_prices:
            continue
        start = float(start_prices[symbol].close)
        end = float(end_prices[symbol].close)
        if start <= 0 or end <= 0:
            continue
        scored.append((symbol, end / start - 1.0))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return [(symbol, score, rank) for rank, (symbol, score) in enumerate(scored[:holdings], 1)]
