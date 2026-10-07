"""P6.1b — Download and verify historical NSE prices for V6 rights entitlements.

Uses NSE's official historical CM/equity endpoint. The downloader tries the
temporary RE symbol with the documented equity-series candidates because RE
securities are not present in the project's ordinary equity universe archives.

Raw responses are archived and SHA-256 hashed. No third-party price is accepted.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import re
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
    "TATACONSUM-RE": (dt.date(2024, 8, 5), dt.date(2024, 8, 12)),
    "ADANI-RE": (dt.date(2025, 11, 25), dt.date(2025, 12, 5)),
}

SERIES_CANDIDATES = ("BE", "EQ", "SM", "T0")
FIELDS = [
    "symbol", "series", "from", "to", "http_status", "status",
    "rows", "sha256", "raw_file", "error",
]


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


def parse_rows(payload):
    if not isinstance(payload, dict):
        return []
    data = payload.get("data", [])
    return data if isinstance(data, list) else []


def row_date(row):
    value = row.get("mTIMESTAMP") or row.get("CH_TIMESTAMP") or row.get("date") or row.get("Date")
    if not value:
        return None
    for fmt in ("%d-%b-%Y", "%d-%b-%Y %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    return None


def first_value(row, *keys):
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return ""


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/154.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/historical/price-and-volume-data-per-security",
    })

    print("PHASE 1A P6.1b — NSE RE HISTORICAL PRICE DOWNLOAD")
    print("Source: NSE official historical CM/equity endpoint")
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
                "series": json.dumps([series], separators=(",", ":")),
                "from": start.strftime("%d-%m-%Y"),
                "to": end.strftime("%d-%m-%Y"),
                "csv": "false",
            }
            url = "https://www.nseindia.com/api/historical/cm/equity?" + urlencode(params)

            try:
                response = session.get(url, timeout=30)
                raw = response.content
                digest = sha256_bytes(raw)
                raw_file = RAW / f"{symbol}_{start:%Y%m%d}_{end:%Y%m%d}_{series}.json"
                save_bytes(raw_file, raw)

                if response.status_code != 200:
                    results.append({
                        "symbol": symbol, "series": series,
                        "from": start.isoformat(), "to": end.isoformat(),
                        "http_status": response.status_code, "status": "HTTP_FAIL",
                        "rows": 0, "sha256": digest,
                        "raw_file": str(raw_file.relative_to(ROOT)), "error": "",
                    })
                    continue

                try:
                    payload = response.json()
                except Exception as exc:
                    results.append({
                        "symbol": symbol, "series": series,
                        "from": start.isoformat(), "to": end.isoformat(),
                        "http_status": response.status_code, "status": "JSON_FAIL",
                        "rows": 0, "sha256": digest,
                        "raw_file": str(raw_file.relative_to(ROOT)), "error": str(exc),
                    })
                    continue

                rows = [
                    r for r in parse_rows(payload)
                    if row_date(r) is not None
                    and start <= row_date(r) <= end
                ]

                results.append({
                    "symbol": symbol, "series": series,
                    "from": start.isoformat(), "to": end.isoformat(),
                    "http_status": response.status_code,
                    "status": "FOUND" if rows else "EMPTY",
                    "rows": len(rows), "sha256": digest,
                    "raw_file": str(raw_file.relative_to(ROOT)), "error": "",
                })

                if rows:
                    out = RAW / f"{symbol}_{start:%Y%m%d}_{end:%Y%m%d}_prices.csv"
                    with out.open("w", newline="", encoding="utf-8") as f:
                        fields = ["date", "symbol", "series", "open", "high", "low", "close", "volume"]
                        writer = csv.DictWriter(f, fieldnames=fields)
                        writer.writeheader()
                        for row in sorted(rows, key=row_date):
                            writer.writerow({
                                "date": row_date(row).isoformat(),
                                "symbol": symbol,
                                "series": first_value(row, "CH_SERIES", "series"),
                                "open": first_value(row, "CH_OPENING_PRICE", "OPEN"),
                                "high": first_value(row, "CH_TRADE_HIGH_PRICE", "HIGH"),
                                "low": first_value(row, "CH_TRADE_LOW_PRICE", "LOW"),
                                "close": first_value(row, "CH_CLOSING_PRICE", "CLOSE"),
                                "volume": first_value(row, "CH_TOT_TRADED_QTY", "VOLUME"),
                            })
                    found = True
                    print(f"{symbol}: FOUND series={series}, rows={len(rows)}")
                    break

                time.sleep(0.5)

            except Exception as exc:
                results.append({
                    "symbol": symbol, "series": series,
                    "from": start.isoformat(), "to": end.isoformat(),
                    "http_status": "", "status": "REQUEST_FAIL",
                    "rows": 0, "sha256": "",
                    "raw_file": "", "error": str(exc),
                })

        if not found:
            print(f"{symbol}: NOT FOUND across series candidates {SERIES_CANDIDATES}")

    RAW.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)

    print()
    found_symbols = {r["symbol"] for r in results if r["status"] == "FOUND"}
    print("Symbols with price evidence:", len(found_symbols), "/", len(TARGETS))

    if found_symbols != set(TARGETS):
        print("STATUS: BLOCKED — one or more RE securities lack official NSE historical rows.")
        return 2

    print("STATUS: PASS — all three RE securities have official NSE historical rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
