"""P6.1b — Download and verify historical NSE prices for V6 rights entitlements."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import os
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "rights_entitlements"
MANIFEST = RAW / "download_manifest.csv"

TARGETS = {
    "GRASIM-RE": (dt.date(2024, 1, 17), dt.date(2024, 1, 23)),
    "TATACON-RE": (dt.date(2024, 8, 5), dt.date(2024, 8, 12)),
    "ADANI-RE": (dt.date(2025, 11, 25), dt.date(2025, 12, 5)),
}

SERIES_CANDIDATES = ("BE", "EQ", "SM", "T0")
FIELDS = ["symbol", "series", "from", "to", "http_status", "content_type",
          "status", "rows", "sha256", "raw_file", "error"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    os.close(fd)
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def parse_csv_rows(raw: bytes):
    text = raw.decode("utf-8-sig", errors="replace")
    low = text.lower()
    if "<html" in low or "access denied" in low:
        raise ValueError("NSE returned HTML/access-denied content")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return []
    def norm(name):
        return " ".join(str(name).strip().lower().split())

    header_map = {norm(h): h for h in reader.fieldnames}
    required = {
        "symbol", "series", "date", "prev close",
        "open price", "high price", "low price", "close price"
    }
    missing = required - set(header_map)
    if missing:
        raise ValueError(
            f"unexpected NSE CSV headers; missing={sorted(missing)} "
            f"actual={reader.fieldnames}"
        )

    rows = []
    for raw in reader:
        rows.append({
            "Symbol": raw.get(header_map["symbol"], "").strip(),
            "Series": raw.get(header_map["series"], "").strip(),
            "Date": raw.get(header_map["date"], "").strip(),
            "Prev Close": raw.get(header_map["prev close"], "").strip(),
            "Open Price": raw.get(header_map["open price"], "").strip(),
            "High Price": raw.get(header_map["high price"], "").strip(),
            "Low Price": raw.get(header_map["low price"], "").strip(),
            "Close Price": raw.get(header_map["close price"], "").strip(),
            "Total Traded Quantity": raw.get(
                header_map.get("total traded quantity", ""), ""
            ).strip() if header_map.get("total traded quantity") else "",
        })
    return rows


def row_date(row):
    value = row.get("Date") or row.get("date") or row.get("CH_TIMESTAMP")
    if not value:
        return None
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    return None


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/154.0 Safari/537.36",
        "Accept": "text/csv,application/csv,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/report-detail/eq_security",
        "X-Requested-With": "XMLHttpRequest",
    })

    print("PHASE 1A P6.1b — NSE RE HISTORICAL PRICE DOWNLOAD")
    print("Endpoint: NSE security-wise historical price-volume")
    print()

    try:
        home = session.get("https://www.nseindia.com/", timeout=30)
        print("NSE session bootstrap:", home.status_code)
    except Exception as exc:
        raise SystemExit(f"BLOCKED: NSE session bootstrap failed: {exc}")

    results = []

    for symbol, (start, end) in TARGETS.items():
        found = False

        for series in SERIES_CANDIDATES:
            params = {
                "symbol": symbol,
                "from": start.strftime("%d-%m-%Y"),
                "to": end.strftime("%d-%m-%Y"),
                "series": series,
                "type": "priceVolumeDeliverable",
                "csv": "true",
            }
            url = (
                "https://www.nseindia.com/api/historicalOR/"
                "generateSecurityWiseHistoricalData?" + urlencode(params)
            )

            try:
                response = session.get(url, timeout=30)
                raw = response.content
                digest = sha256_bytes(raw)
                content_type = response.headers.get("Content-Type", "")
                raw_file = RAW / f"{symbol}_{start:%Y%m%d}_{end:%Y%m%d}_{series}.csv"
                save_bytes(raw_file, raw)

                if response.status_code != 200:
                    status = "HTTP_FAIL"
                    rows = []
                    error = ""
                else:
                    try:
                        rows = [
                            r for r in parse_csv_rows(raw)
                            if row_date(r) is not None
                            and start <= row_date(r) <= end
                        ]
                        status = "FOUND" if rows else "EMPTY"
                        error = ""
                    except Exception as exc:
                        rows = []
                        status = "PARSE_FAIL"
                        error = str(exc)
                        print(
                            f"{symbol} {series}: HTTP={response.status_code} "
                            f"Content-Type={content_type!r} "
                            f"body_prefix={raw[:160]!r}"
                        )

                results.append({
                    "symbol": symbol, "series": series,
                    "from": start.isoformat(), "to": end.isoformat(),
                    "http_status": response.status_code,
                    "content_type": content_type,
                    "status": status, "rows": len(rows),
                    "sha256": digest,
                    "raw_file": str(raw_file.relative_to(ROOT)),
                    "error": error,
                })

                if rows:
                    out = RAW / f"{symbol}_{start:%Y%m%d}_{end:%Y%m%d}_prices.csv"
                    with out.open("w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=["date", "symbol", "series",
                                        "open", "high", "low", "close",
                                        "prev_close", "volume"],
                        )
                        writer.writeheader()
                        for row in sorted(rows, key=row_date):
                            writer.writerow({
                                "date": row_date(row).isoformat(),
                                "symbol": symbol,
                                "series": row.get("Series", series),
                                "open": row.get("Open Price", ""),
                                "high": row.get("High Price", ""),
                                "low": row.get("Low Price", ""),
                                "close": row.get("Close Price", ""),
                                "prev_close": row.get("Prev Close", ""),
                                "volume": row.get("Total Traded Quantity", ""),
                            })
                    print(f"{symbol}: FOUND series={series}, rows={len(rows)}")
                    found = True
                    break

                time.sleep(0.5)

            except Exception as exc:
                results.append({
                    "symbol": symbol, "series": series,
                    "from": start.isoformat(), "to": end.isoformat(),
                    "http_status": "", "content_type": "",
                    "status": "REQUEST_FAIL", "rows": 0,
                    "sha256": "", "raw_file": "", "error": str(exc),
                })

        if not found:
            print(f"{symbol}: NOT FOUND across series candidates {SERIES_CANDIDATES}")

    RAW.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)

    found_symbols = {r["symbol"] for r in results if r["status"] == "FOUND"}
    print()
    print("Symbols with price evidence:", len(found_symbols), "/", len(TARGETS))

    if found_symbols != set(TARGETS):
        print("STATUS: BLOCKED — one or more RE securities lack official NSE historical rows.")
        return 2

    print("STATUS: PASS — all three RE securities have official NSE historical rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
