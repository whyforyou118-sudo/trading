"""Point-in-time NIFTY 50 membership reconstruction audit.

This validator intentionally refuses to infer the initial 50 constituents from
transition rows alone. A complete PIT ledger needs an authoritative baseline
snapshot before the first transition.
"""
from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "data" / "reference"
TRANSITIONS = REFERENCE / "nifty50_membership.csv"
BASELINE = REFERENCE / "nifty50_baseline.csv"
OUT = ROOT / "audits" / "pit_membership_reconstruction.csv"


@dataclass(frozen=True)
class Security:
    symbol: str
    company_name: str
    isin: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_baseline() -> dict[str, Security]:
    if not BASELINE.exists():
        raise RuntimeError(
            "authoritative baseline snapshot is missing; transition rows alone "
            "cannot reconstruct the first PIT NIFTY 50 state"
        )

    rows = read_csv(BASELINE)
    required = {"symbol", "company_name", "isin"}
    if not rows:
        raise RuntimeError("baseline snapshot is empty")
    missing = required - set(rows[0])
    if missing:
        raise RuntimeError(f"baseline columns missing: {sorted(missing)}")

    securities = {}
    for row in rows:
        sec = Security(row["symbol"].strip(), row["company_name"].strip(), row["isin"].strip())
        if not sec.symbol or not sec.isin:
            raise RuntimeError("baseline contains blank symbol or ISIN")
        if sec.symbol in securities:
            raise RuntimeError(f"duplicate baseline symbol: {sec.symbol}")
        securities[sec.symbol] = sec

    if len(securities) != 50:
        raise RuntimeError(f"baseline must contain exactly 50 securities; found {len(securities)}")

    isins = [s.isin for s in securities.values()]
    dup_isins = [isin for isin, n in Counter(isins).items() if n > 1]
    if dup_isins:
        raise RuntimeError(f"duplicate baseline ISINs: {dup_isins}")

    return securities


def load_transitions() -> list[dict[str, str]]:
    rows = read_csv(TRANSITIONS)
    if not rows:
        raise RuntimeError("transition ledger is empty")

    required = {"effective_date", "symbol", "company_name", "isin", "action"}
    missing = required - set(rows[0])
    if missing:
        raise RuntimeError(f"transition columns missing: {sorted(missing)}")

    for row in rows:
        if row["action"] not in {"INCLUSION", "EXCLUSION"}:
            raise RuntimeError(f"unknown action: {row['action']}")
        try:
            date.fromisoformat(row["effective_date"])
        except ValueError:
            raise RuntimeError(f"invalid effective date: {row['effective_date']}")

    return sorted(rows, key=lambda r: (r["effective_date"], r["symbol"], r["action"]))


def reconstruct() -> list[dict[str, object]]:
    members = load_baseline()
    transitions = load_transitions()

    output = []
    grouped_dates = sorted({r["effective_date"] for r in transitions})

    for effective_date in grouped_dates:
        rows = [r for r in transitions if r["effective_date"] == effective_date]

        # Apply all changes atomically for the effective date.
        proposed = dict(members)
        errors = []

        for row in rows:
            symbol, isin, action = row["symbol"], row["isin"], row["action"]
            if action == "INCLUSION":
                if symbol in proposed:
                    errors.append(f"inclusion already present: {symbol}")
                if any(s.isin == isin for s in proposed.values()):
                    errors.append(f"inclusion ISIN already present: {isin}")
                proposed[symbol] = Security(symbol, row["company_name"], isin)
            else:
                if symbol not in proposed:
                    errors.append(f"exclusion absent from current state: {symbol}")
                else:
                    current = proposed[symbol]
                    if current.isin != isin:
                        errors.append(
                            f"exclusion ISIN mismatch for {symbol}: "
                            f"ledger={isin}, current={current.isin}"
                        )
                    del proposed[symbol]

        duplicate_isins = [
            isin for isin, count in Counter(s.isin for s in proposed.values()).items()
            if count > 1
        ]
        if duplicate_isins:
            errors.append(f"duplicate ISINs after transition: {duplicate_isins}")

        count_ok = len(proposed) == 50
        if not count_ok:
            errors.append(f"membership count={len(proposed)}, expected 50")

        output.append({
            "effective_date": effective_date,
            "transition_rows": len(rows),
            "member_count": len(proposed),
            "duplicate_isins": ";".join(duplicate_isins),
            "status": "PASS" if not errors else "FAIL",
            "errors": " | ".join(errors),
        })

        if errors:
            # Stop at the first impossible state; later states depend on it.
            break

        members = proposed

    return output


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    try:
        results = reconstruct()
    except RuntimeError as exc:
        print(f"PIT MEMBERSHIP: BLOCKED — {exc}")
        return 2

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "effective_date",
                "transition_rows",
                "member_count",
                "duplicate_isins",
                "status",
                "errors",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    failures = [r for r in results if r["status"] == "FAIL"]
    print(f"Effective states checked: {len(results)}")
    if failures:
        print("PIT MEMBERSHIP: FAIL")
        print(failures[0]["errors"])
        return 1

    print("PIT MEMBERSHIP: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
