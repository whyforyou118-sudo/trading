"""Build the Phase 1A PIT decision table from frozen strategy inputs.

This artifact is an audit input, not a performance result. It records the
information dates used by the frozen quarterly Top-5 signal:
- decision_date: quarterly rebalance decision date
- available_from/to: membership-state validity interval
- signal_source_date: last month-end close used by the 12M/1M-skip signal
- execution_date: next actual trading day

No publication date is inferred. Membership availability means the reconstructed
membership state is effective on the decision date; external publication evidence
remains a separate Phase 0.5 gate.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def trading_days(path: Path):
    return sorted(
        dt.date.fromisoformat(r["date"])
        for r in read(path)
        if r.get("is_trading_day", "").lower() == "true"
    )

def membership_intervals(baseline_path: Path, transitions_path: Path, events_path: Path, dates: list[dt.date]):
    baseline = {r["symbol"]: r["isin"] for r in read(baseline_path)}
    transitions = read(transitions_path)
    events = read(events_path) if events_path.exists() else []
    by_symbol = {s: [] for s in baseline}

    all_dates = sorted(set(
        [dt.date.fromisoformat(r["effective_date"]) for r in transitions]
        + [dt.date.fromisoformat(r["event_date"]) for r in events if r.get("apply_to_membership_state", "").lower() == "true"]
    ))
    state = dict(baseline)
    for i, d in enumerate(all_dates):
        if d <= dt.date(2017, 3, 31):
            continue
        for e in events:
            if e.get("apply_to_membership_state", "").lower() == "true" and dt.date.fromisoformat(e["event_date"]) == d:
                if e["symbol"] in state and state[e["symbol"]] == e["old_isin"]:
                    state[e["symbol"]] = e["new_isin"]
        for r in transitions:
            if dt.date.fromisoformat(r["effective_date"]) != d:
                continue
            if r["action"] == "INCLUSION":
                state[r["symbol"]] = r["isin"]
            elif r["action"] == "EXCLUSION":
                state.pop(r["symbol"], None)

        next_date = all_dates[i + 1] if i + 1 < len(all_dates) else None
        available_to = (next_date - dt.timedelta(days=1)) if next_date else None
        for symbol in state:
            by_symbol.setdefault(symbol, []).append((d, available_to, state[symbol]))
    return by_symbol

def quarter_ends(days: list[dt.date], start: dt.date, end: dt.date):
    return [d for d in days if start <= d <= end and d.month in (3, 6, 9, 12) and (d + dt.timedelta(days=1)).month != d.month]

def previous_month_end(days: list[dt.date], d: dt.date):
    candidates = [x for x in days if x < d and (x.year, x.month) != (d.year, d.month)]
    return max(candidates)

def main() -> int:
    ap = argparse.ArgumentParser(description="Build Phase 1A PIT decision table.")
    ap.add_argument("--top5", type=Path, default=ROOT / "audits/phase05_top5_feasibility.csv")
    ap.add_argument("--calendar", type=Path, default=ROOT / "audits/nse_trading_calendar_v3.csv")
    ap.add_argument("--baseline", type=Path, default=ROOT / "data/reference/nifty50_baseline.csv")
    ap.add_argument("--membership", type=Path, default=ROOT / "data/reference/nifty50_membership.csv")
    ap.add_argument("--events", type=Path, default=ROOT / "data/reference/security_identity_events.csv")
    ap.add_argument("--report", type=Path, default=ROOT / "audits/phase1a_pit_decision_table.csv")
    args = ap.parse_args()

    for p in [args.top5, args.calendar, args.baseline, args.membership]:
        if not p.exists():
            raise SystemExit(f"BLOCKED: missing required artifact: {p}")

    rows = read(args.top5)
    days = trading_days(args.calendar)
    intervals = membership_intervals(args.baseline, args.membership, args.events, days)
    out = []

    for r in rows:
        decision = dt.date.fromisoformat(r["rebalance_date"])
        execution = dt.date.fromisoformat(r["execution_date"])
        source = previous_month_end(days, decision)
        symbol = r["symbol"]
        matches = [
            x for x in intervals.get(symbol, [])
            if x[0] <= decision and (x[1] is None or decision <= x[1])
        ]
        if len(matches) != 1:
            raise SystemExit(f"BLOCKED: membership state not uniquely resolved for {symbol} at {decision}")
        available_from, available_to, _ = matches[0]
        out.append({
            "decision_date": decision.isoformat(),
            "symbol": symbol,
            "eligible": "true",
            "available_from": available_from.isoformat(),
            "available_to": available_to.isoformat() if available_to else "",
            "signal_source_date": source.isoformat(),
            "execution_date": execution.isoformat(),
        })

    if not out:
        raise SystemExit("BLOCKED: no PIT decision rows produced")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)

    print("PHASE 1A PIT DECISION TABLE")
    print(f"Rows: {len(out)}")
    print(f"Decision dates: {len(set(r['decision_date'] for r in out))}")
    print(f"Artifact: {args.report}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
