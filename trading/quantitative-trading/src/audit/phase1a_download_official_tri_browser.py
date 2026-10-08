"""Download the frozen Phase 1A TRI benchmarks through a real Chrome session.

This is a transport fallback for environments where the official
niftyindices.com API returns an HTML bot/challenge page to requests/curl.
It does not change the benchmark definition, endpoint, dates, or output
schema. The browser session calls the same official NSE Indices TRI method.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import tempfile
from pathlib import Path

BASE = "https://www.niftyindices.com"
PAGE_URL = f"{BASE}/reports/historical-data"
TRI_URL = f"{BASE}/Backpage.aspx/getTotalReturnIndexString"

START = dt.date(2018, 1, 1)
END = dt.date(2025, 12, 31)
OUT_DIR = Path("data/reference")

TARGETS = {
    "NIFTY 50": "nifty50_tri.csv",
    "NIFTY50 EQUAL WEIGHT": "nifty50_equal_weight_tri.csv",
}


def request_payload(index_name: str, start: dt.date, end: dt.date) -> dict:
    inner = (
        "{'name':'"
        + index_name
        + "','startDate':'"
        + start.strftime("%d %b %Y")
        + "','endDate':'"
        + end.strftime("%d %b %Y")
        + "','indexName':'"
        + index_name
        + "'}"
    )
    return {"cinfo": inner}


def parse_response(text: str, index_name: str) -> list[dict]:
    raw = text.lstrip("\ufeff").strip()
    if not raw or raw[:1] not in "{[":
        raise RuntimeError(
            f"Official TRI browser response was not JSON for {index_name}: "
            f"{raw[:500]!r}"
        )

    obj = json.loads(raw)
    if isinstance(obj, dict):
        rows = obj.get("d", obj)
    else:
        rows = obj

    if isinstance(rows, str):
        rows = json.loads(rows)

    if not isinstance(rows, list):
        raise RuntimeError(
            f"Unexpected official TRI payload for {index_name}: "
            f"{type(rows).__name__}"
        )

    output = []
    for row in rows:
        raw_date = row.get("Date") or row.get("HistoricalDate")
        raw_tri = row.get("TotalReturnsIndex")
        if raw_date is None or raw_tri in (None, ""):
            continue
        parsed = dt.datetime.strptime(str(raw_date), "%d %b %Y").date()
        if START <= parsed <= END:
            output.append(
                {
                    "date": parsed.isoformat(),
                    "value": float(raw_tri),
                    "source": (
                        "Nifty Indices Historical Data — "
                        "Total Returns Index Values"
                    ),
                    "source_reference": PAGE_URL,
                }
            )

    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "value", "source", "source_reference"]
    fd, tmp = tempfile.mkstemp(
        prefix=path.stem + ".", suffix=".csv", dir=str(path.parent)
    )
    os.close(fd)
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def fetch_with_browser(index_name: str) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for the browser transport fallback. "
            "Run: python -m pip install playwright"
        ) from exc

    all_rows: dict[str, dict] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="chrome",
            headless=False,
        )
        context = browser.new_context(
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        try:
            print(f"Opening official NSE Indices page for browser session: {PAGE_URL}")
            page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)

            current = START
            while current <= END:
                chunk_end = min(
                    current + dt.timedelta(days=364),
                    END,
                )
                payload = request_payload(index_name, current, chunk_end)
                print(
                    f"Browser TRI request: {index_name} | "
                    f"{current} -> {chunk_end}"
                )

                result = page.evaluate(
                    """async ({url, payload}) => {
                        const response = await fetch(url, {
                            method: "POST",
                            credentials: "include",
                            headers: {
                                "Content-Type": "application/json; charset=UTF-8",
                                "X-Requested-With": "XMLHttpRequest",
                                "Accept": "*/*"
                            },
                            body: JSON.stringify(payload)
                        });
                        return {
                            status: response.status,
                            contentType: response.headers.get("content-type"),
                            text: await response.text()
                        };
                    }""",
                    {"url": TRI_URL, "payload": payload},
                )

                if result["status"] != 200:
                    raise RuntimeError(
                        f"Official TRI browser request returned HTTP "
                        f"{result['status']} for {index_name}: "
                        f"{result['text'][:500]!r}"
                    )

                chunk = parse_response(result["text"], index_name)
                if not chunk:
                    raise RuntimeError(
                        f"No official TRI observations returned for "
                        f"{index_name}: {current} -> {chunk_end}"
                    )

                for row in chunk:
                    all_rows[row["date"]] = row

                current = chunk_end + dt.timedelta(days=1)

        finally:
            browser.close()

    rows = [all_rows[key] for key in sorted(all_rows)]
    if not rows:
        raise RuntimeError(f"No usable official TRI observations for {index_name}")
    return rows


def main() -> int:
    for index_name, filename in TARGETS.items():
        rows = fetch_with_browser(index_name)
        path = OUT_DIR / filename
        write_csv(path, rows)
        print(
            f"{index_name}: {len(rows)} observations | "
            f"{rows[0]['date']} -> {rows[-1]['date']} | {path}"
        )

    print("STATUS: PASS — official gross TRI artifacts downloaded via Chrome.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
