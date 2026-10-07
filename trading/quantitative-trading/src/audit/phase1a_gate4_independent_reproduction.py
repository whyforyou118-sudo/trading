"""Phase 1A Gate 4: independent second implementation reproduction.

This implementation is deliberately written independently of the Phase 0.5
Top-5 builder: chronological loops and dictionaries, explicit month arithmetic,
and no reuse/import of the first implementation.

It reproduces the frozen ranking specification only:
- NIFTY50 PIT membership at decision date
- 12-month formation with 1-month skip
- quarterly decision dates
- top 5 by momentum
- next actual trading-day execution date

The comparison is against the frozen Phase 0.5 artifact, but the independent
calculation does not import or call its functions.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "config/phase05_config.json"
CAL = ROOT / "audits/nse_trading_calendar_v3.csv"
MANIFEST = ROOT / "data/raw/prices/download_manifest.csv"
BASELINE = ROOT / "data/reference/nifty50_baseline.csv"
TRANSITIONS = ROOT / "data/reference/nifty50_membership.csv"
EVENTS = ROOT / "data/reference/security_identity_events.csv"
REFERENCE = ROOT / "audits/phase05_top5_feasibility.csv"
OUT = ROOT / "audits/phase1a_gate4_reproduction.csv"


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def nse_prices(path: Path):
    def consume(raw):
        reader = csv.DictReader(io.StringIO(raw.read().decode("utf-8-sig")))
        fields = set(reader.fieldnames or [])
        if {"SYMBOL", "SERIES", "OPEN", "CLOSE"} <= fields:
            symbol, series, op, close = "SYMBOL", "SERIES", "OPEN", "CLOSE"
        elif {"TckrSymb", "SctySrs", "OpnPric", "ClsPric"} <= fields:
            symbol, series, op, close = "TckrSymb", "SctySrs", "OpnPric", "ClsPric"
        else:
            raise RuntimeError("unsupported NSE price schema: " + path.name)
        result = {}
        for row in reader:
            if (row.get(series) or "").strip() != "EQ":
                continue
            name = (row.get(symbol) or "").strip()
            try:
                result[name] = (float(row[op]), float(row[close]))
            except (TypeError, ValueError):
                continue
        return result

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            csvs = [x for x in archive.namelist() if x.lower().endswith(".csv")]
            if len(csvs) != 1:
                raise RuntimeError("expected one CSV in " + path.name)
            with archive.open(csvs[0]) as raw:
                return consume(raw)
    with path.open("rb") as raw:
        return consume(raw)


def trading_days():
    return sorted(
        dt.date.fromisoformat(x["date"])
        for x in rows(CAL)
        if x.get("is_trading_day", "").lower() == "true"
    )


def month_end(days, year, month):
    candidates = [d for d in days if d.year == year and d.month == month]
    if not candidates:
        raise RuntimeError(f"no trading month-end for {year}-{month:02d}")
    return candidates[-1]


def prior_month(year, month, months_back):
    value = year * 12 + (month - 1) - months_back
    return value // 12, value % 12 + 1


def membership_at(baseline, transitions, identity_events, decision):
    state = {
        symbol: dict(value)
        for symbol, value in baseline.items()
    }

    actions = []
    for event in identity_events:
        date = dt.date.fromisoformat(event["event_date"])
        if date <= decision and event.get("apply_to_membership_state", "").lower() == "true":
            actions.append((date, "identity", event))

    for change in transitions:
        date = dt.date.fromisoformat(change["effective_date"])
        if date <= decision:
            actions.append((date, "membership", change))

    for _, kind, event in sorted(actions, key=lambda x: (x[0], x[1])):
        if kind == "identity":
            symbol = event["symbol"]
            if symbol in state and state[symbol]["isin"] == event["old_isin"]:
                state[symbol]["isin"] = event["new_isin"]
        elif event["action"] == "INCLUSION":
            state[event["symbol"]] = {
                "company_name": event["company_name"],
                "isin": event["isin"],
            }
        elif event["action"] == "EXCLUSION":
            state.pop(event["symbol"], None)

    return state


def independent_selection():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    days = trading_days()
    manifest = {x["date"]: x for x in rows(MANIFEST)}
    baseline = {
        x["symbol"]: {"company_name": x["company_name"], "isin": x["isin"]}
        for x in rows(BASELINE)
    }
    transitions = rows(TRANSITIONS)
    identity_events = rows(EVENTS) if EVENTS.exists() else []

    # Reproduce the exact frozen Phase 0.5 decision-date sample.
    # Do not infer an additional 2025-12-31 decision: the frozen feasibility
    # artifact ends at 2025-09-30 because its required next-session execution
    # data ends at 2025-10-01.
    reference_dates = sorted(set(x["rebalance_date"] for x in rows(REFERENCE)))
    decision_dates = [dt.date.fromisoformat(x) for x in reference_dates]
    if len(decision_dates) != 31:
        raise RuntimeError(
            f"frozen reference must contain exactly 31 decision dates; got {len(decision_dates)}"
        )
    cache = {}

    def price_on(day):
        key = day.isoformat()
        if key not in cache:
            item = manifest.get(key)
            if item is None:
                raise RuntimeError("price manifest missing " + key)
            file_path = ROOT / "data/raw/prices" / item["format"] / Path(item["url"]).name
            cache[key] = nse_prices(file_path)
        return cache[key]

    results = []
    holdings = int(cfg["primary_holdings"])

    for decision in decision_dates:
        y, m = prior_month(decision.year, decision.month, 1)
        formation_end = month_end(days, y, m)

        sy, sm = prior_month(decision.year, decision.month, 13)
        formation_start = month_end(days, sy, sm)

        execution = next((d for d in days if d > decision), None)
        if execution is None:
            raise RuntimeError("missing execution day after " + decision.isoformat())

        end_prices = price_on(formation_end)
        start_prices = price_on(formation_start)
        eligible = membership_at(baseline, transitions, identity_events, decision)

        ranked = []
        for symbol in sorted(eligible):
            if symbol not in end_prices or symbol not in start_prices:
                continue
            end_close = end_prices[symbol][1]
            start_close = start_prices[symbol][1]
            if end_close <= 0 or start_close <= 0:
                continue
            ranked.append((end_close / start_close - 1.0, symbol))

        # Deterministic tie rule: descending score, then ascending symbol.
        ranked.sort(key=lambda x: (-x[0], x[1]))
        for rank, (score, symbol) in enumerate(ranked[:holdings], 1):
            results.append({
                "rebalance_date": decision.isoformat(),
                "execution_date": execution.isoformat(),
                "rank": str(rank),
                "symbol": symbol,
                "momentum": f"{score:.15g}",
            })

    return results


def main():
    independent = independent_selection()
    reference = rows(REFERENCE)

    ref = {
        (r["rebalance_date"], r["rank"]): r["symbol"]
        for r in reference
    }
    ind = {
        (r["rebalance_date"], r["rank"]): r["symbol"]
        for r in independent
    }

    keys = sorted(set(ref) | set(ind))
    mismatches = [
        (date, rank, ref.get((date, rank)), ind.get((date, rank)))
        for date, rank in keys
        if ref.get((date, rank)) != ind.get((date, rank))
    ]

    out = []
    for date, rank in keys:
        out.append({
            "rebalance_date": date,
            "rank": rank,
            "reference_symbol": ref.get((date, rank), ""),
            "independent_symbol": ind.get((date, rank), ""),
            "status": "PASS" if ref.get((date, rank)) == ind.get((date, rank)) else "FAIL",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out[0].keys())
        writer.writeheader()
        writer.writerows(out)

    expected = 31 * 5
    print("PHASE 1A GATE 4 — INDEPENDENT SECOND IMPLEMENTATION")
    print(f"Independent rows: {len(independent)}")
    print(f"Reference rows: {len(reference)}")
    print(f"Expected rows: {expected}")
    print(f"Symbol/rank mismatches: {len(mismatches)}")
    if mismatches:
        for item in mismatches[:20]:
            print("MISMATCH", item)
        print("STATUS: FAIL — resolve specification/data ambiguity before performance.")
        return 1
    if len(independent) != expected or len(reference) != expected:
        print("STATUS: FAIL — incomplete 31-date × 5-rank reproduction.")
        return 1
    print("STATUS: PASS — all 31 quarterly Top-5 selections reproduce exactly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
