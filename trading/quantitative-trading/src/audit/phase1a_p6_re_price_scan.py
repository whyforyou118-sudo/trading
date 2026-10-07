"""P6.1 — Scan downloaded NSE bhavcopies for the three V6 rights-entitlement instruments.

No external price source is accepted here. The scanner searches the project's
own immutable NSE CM bhavcopy archives for the RE symbols and reports every
matching trading row in the relevant entitlement window.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRICE_ROOT = ROOT / "data" / "raw" / "prices"

TARGETS = {
    "GRASIM-RE": (dt.date(2024, 1, 1), dt.date(2024, 2, 15)),
    "TATACONSUM-RE": (dt.date(2024, 7, 15), dt.date(2024, 9, 1)),
    "ADANI-RE": (dt.date(2025, 11, 20), dt.date(2025, 12, 15)),
}


def parse_date(value: str) -> dt.date:
    value = value.strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(value)


def find_column(fields, *names):
    normalized = {f.strip().lower(): f for f in fields}
    for name in names:
        if name.lower() in normalized:
            return normalized[name.lower()]
    return None


def iter_csv_members(zpath: Path):
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if name.lower().endswith(".csv"):
                with z.open(name) as raw:
                    yield name, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")


def scan_zip(zpath: Path, fallback_date: dt.date | None):
    out = []
    try:
        members = iter_csv_members(zpath)
        for member_name, stream in members:
            reader = csv.DictReader(stream)
            if not reader.fieldnames:
                continue

            symbol_col = find_column(reader.fieldnames, "SYMBOL", "Symbol")
            date_col = find_column(reader.fieldnames, "TIMESTAMP", "Date", "DATE")
            series_col = find_column(reader.fieldnames, "SERIES", "Series")
            open_col = find_column(reader.fieldnames, "OPEN", "OPEN_PRICE", "Open Price")
            high_col = find_column(reader.fieldnames, "HIGH", "High Price")
            low_col = find_column(reader.fieldnames, "LOW", "Low Price")
            close_col = find_column(reader.fieldnames, "CLOSE", "CLOSE_PRICE", "Close Price")
            volume_col = find_column(reader.fieldnames, "TOTTRDQTY", "TOTALTRADERVOLUME", "Total Traded Quantity")

            if not symbol_col or not open_col:
                continue

            for row in reader:
                symbol = (row.get(symbol_col) or "").strip().upper()
                if symbol not in TARGETS:
                    continue

                raw_date = (row.get(date_col) or "").strip() if date_col else ""
                try:
                    day = parse_date(raw_date) if raw_date else fallback_date
                except ValueError:
                    continue

                if day is None:
                    continue

                start, end = TARGETS[symbol]
                if not start <= day <= end:
                    continue

                out.append({
                    "date": day.isoformat(),
                    "symbol": symbol,
                    "series": (row.get(series_col) or "").strip() if series_col else "",
                    "open": (row.get(open_col) or "").strip(),
                    "high": (row.get(high_col) or "").strip() if high_col else "",
                    "low": (row.get(low_col) or "").strip() if low_col else "",
                    "close": (row.get(close_col) or "").strip() if close_col else "",
                    "volume": (row.get(volume_col) or "").strip() if volume_col else "",
                    "archive": str(zpath.relative_to(ROOT)),
                    "member": member_name,
                })
    except zipfile.BadZipFile:
        return []
    return out


def infer_date_from_filename(path: Path):
    import re
    m = re.search(r"(20\d{6})", path.name)
    if m:
        try:
            return dt.datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            pass
    m = re.search(r"cm(\d{2})([A-Za-z]{3})(20\d{2})", path.name, re.I)
    if m:
        try:
            return dt.datetime.strptime("".join(m.groups()), "%d%b%Y").date()
        except ValueError:
            pass
    return None


def main():
    archives = sorted(PRICE_ROOT.rglob("*.zip"))
    if not archives:
        raise SystemExit(f"BLOCKED: no NSE bhavcopy archives found under {PRICE_ROOT}")

    rows = []
    for zpath in archives:
        fallback = infer_date_from_filename(zpath)
        rows.extend(scan_zip(zpath, fallback))

    rows.sort(key=lambda r: (r["symbol"], r["date"]))

    print("PHASE 1A P6.1 — RIGHTS ENTITLEMENT PRICE SCAN")
    print(f"Archives scanned: {len(archives)}")
    print(f"RE rows found: {len(rows)}")
    print()

    for row in rows:
        print(
            f'{row["date"]} | {row["symbol"]} | series={row["series"]} | '
            f'open={row["open"]} | high={row["high"]} | low={row["low"]} | '
            f'close={row["close"]} | volume={row["volume"]}'
        )

    print()
    for symbol, (start, end) in TARGETS.items():
        matching = [r for r in rows if r["symbol"] == symbol]
        if not matching:
            print(f"BLOCKED: no local NSE bhavcopy row found for {symbol} in {start}..{end}")
        else:
            print(f"{symbol}: {len(matching)} rows; first={matching[0]['date']}; last={matching[-1]['date']}")

    if len({r["symbol"] for r in rows}) < len(TARGETS):
        print("STATUS: BLOCKED — required RE price evidence is missing from local NSE archives.")
        return 2

    print("STATUS: PASS — all three RE instruments have local NSE price evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
