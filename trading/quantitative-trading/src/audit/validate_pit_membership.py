"""Point-in-time NIFTY 50 membership reconstruction audit."""
from __future__ import annotations
import csv
import datetime
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "data" / "reference"
RAW = ROOT / "data" / "raw" / "prices"
TRANSITIONS = REFERENCE / "nifty50_membership.csv"
BASELINE = REFERENCE / "nifty50_baseline.csv"
OUT = ROOT / "audits" / "pit_membership_reconstruction.csv"

@dataclass(frozen=True)
class Security:
    symbol: str
    company_name: str
    isin: str

def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def resolve_isins(symbols):
    found = {}
    paths = sorted(list(RAW.rglob("*.csv")) + list(RAW.rglob("*.zip")))
    for path in paths:
        try:
            if path.suffix.lower() == ".zip":
                with zipfile.ZipFile(path) as zf:
                    names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                    streams = [zf.open(n, "r") for n in names]
            else:
                streams = [path.open("rb")]
            for stream in streams:
                try:
                    text = stream.read().decode("utf-8-sig")
                    reader = csv.DictReader(text.splitlines())
                    cols = set(reader.fieldnames or [])
                    if "SYMBOL" not in cols or "ISIN" not in cols:
                        continue
                    for row in reader:
                        sym = (row.get("SYMBOL") or "").strip()
                        if sym not in symbols or (row.get("SERIES") or "").strip() != "EQ":
                            continue
                        isin = (row.get("ISIN") or "").strip()
                        if isin:
                            if sym in found and found[sym] != isin:
                                raise RuntimeError(f"conflicting ISINs for {sym}: {found[sym]} vs {isin}")
                            found[sym] = isin
                finally:
                    stream.close()
        except (zipfile.BadZipFile, UnicodeDecodeError):
            continue
    return found

def load_baseline():
    if not BASELINE.exists():
        raise RuntimeError("authoritative baseline snapshot is missing")
    rows = read_csv(BASELINE)
    required = {"symbol", "company_name", "source", "source_reference"}
    if not rows:
        raise RuntimeError("baseline snapshot is empty")
    missing = required - set(rows[0])
    if missing:
        raise RuntimeError(f"baseline columns missing: {sorted(missing)}")
    securities = {}
    for row in rows:
        symbol = row["symbol"].strip()
        if not symbol or symbol in securities:
            raise RuntimeError(f"invalid or duplicate baseline symbol: {symbol}")
        securities[symbol] = Security(symbol, row["company_name"].strip(), row.get("isin", "").strip())
    if len(securities) != 51:
        raise RuntimeError(f"2017-03-31 baseline expected 51 security rows from NSE Fact Book; found {len(securities)}")
    return securities

def load_transitions():
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
        datetime.date.fromisoformat(row["effective_date"])
    return sorted(rows, key=lambda r: (r["effective_date"], r["symbol"], r["action"]))

def reconstruct():
    members = load_baseline()
    transitions = load_transitions()

    # Resolve missing baseline ISINs from raw exchange files when available.
    missing_symbols = {s for s, sec in members.items() if not sec.isin}
    if missing_symbols:
        resolved = resolve_isins(missing_symbols)
        members = {
            s: Security(sec.symbol, sec.company_name, resolved.get(s, sec.isin))
            for s, sec in members.items()
        }

    unresolved = [s for s, sec in members.items() if not sec.isin]
    if unresolved:
        raise RuntimeError("baseline ISINs unresolved from raw exchange data: " + ", ".join(sorted(unresolved)))

    output = []
    for effective_date in sorted({r["effective_date"] for r in transitions}):
        rows = [r for r in transitions if r["effective_date"] == effective_date]
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
                        errors.append(f"exclusion ISIN mismatch for {symbol}: ledger={isin}, current={current.isin}")
                    del proposed[symbol]

        duplicate_isins = [i for i,n in Counter(s.isin for s in proposed.values()).items() if n > 1]
        if duplicate_isins:
            errors.append(f"duplicate ISINs after transition: {duplicate_isins}")

        # Historical exception: NSE Fact Book lists 51 rows on 2017-03-31
        # because both Tata Motors and Tata Motors DVR appear. The Sep-2017
        # transition removes the DVR and the resulting state is 50.
        allowed_counts = {51} if effective_date < "2017-09-29" else {50}
        if len(proposed) not in allowed_counts:
            errors.append(f"membership count={len(proposed)}, expected one of {sorted(allowed_counts)}")

        output.append({
            "effective_date": effective_date,
            "transition_rows": len(rows),
            "member_count": len(proposed),
            "duplicate_isins": ";".join(duplicate_isins),
            "status": "PASS" if not errors else "FAIL",
            "errors": " | ".join(errors),
        })
        if errors:
            break
        members = proposed
    return output

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        results = reconstruct()
    except RuntimeError as exc:
        print(f"PIT MEMBERSHIP: BLOCKED — {exc}")
        return 2
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["effective_date","transition_rows","member_count","duplicate_isins","status","errors"])
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
