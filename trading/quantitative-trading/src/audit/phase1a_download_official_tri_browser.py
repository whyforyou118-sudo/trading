"""Acquire the frozen TRI benchmarks through the official NSE Historical Data UI.

This module deliberately uses the visible "Total returns Index Values" workflow
instead of the legacy internal API. It never reconstructs TRI values.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import tempfile
from pathlib import Path

BASE = "https://www.niftyindices.com"
PAGE_URL = f"{BASE}/reports"

START = dt.date(2018, 1, 1)
END = dt.date(2025, 12, 31)
OUT_DIR = Path("data/reference")

TARGETS = {
    "NIFTY 50": ("Broad Market Indices", "nifty50_tri.csv"),
    "NIFTY50 EQUAL WEIGHT": ("Strategy Indices", "nifty50_equal_weight_tri.csv"),
}

RETURN_TYPE_ID = "ddlHistoricalreturntypee"
RETURN_SUBINDEX_ID = "ddlHistoricalreturntypeeSubindex"
RETURN_INDEX_ID = "ddlHistoricalreturntypeeindex"


def _options(page, selector: str) -> list[dict]:
    return page.locator(selector).locator("option").evaluate_all(
        "(els) => els.map(e => ({text:(e.textContent||'').trim(), value:e.value}))"
    )


def _select_by_text(page, selector: str, wanted: str) -> None:
    loc = page.locator(selector)
    opts = _options(page, selector)
    match = next((o for o in opts if o["text"].upper() == wanted.upper()), None)
    if match is None:
        match = next((o for o in opts if wanted.upper() in o["text"].upper()), None)
    if match is None:
        raise RuntimeError(
            f"NSE UI option not found: {wanted!r}; "
            f"selector={selector}; options={[o['text'] for o in opts]!r}"
        )
    loc.select_option(value=match["value"], force=True)


def _visible_input_inventory(page) -> list[dict]:
    return page.locator("input:visible").evaluate_all(
        """els => els.map((e,i) => ({
            i, id:e.id||'', name:e.name||'', type:e.type||'',
            value:e.value||'', placeholder:e.placeholder||'',
            className:e.className||'', aria:e.getAttribute('aria-label')||''
        }))"""
    )


def _find_date_inputs(page):
    inputs = page.locator("input:visible")
    scored = []
    for i in range(inputs.count()):
        e = inputs.nth(i)
        meta = e.evaluate(
            """e => ({
                id:e.id||'', name:e.name||'', type:e.type||'',
                value:e.value||'', placeholder:e.placeholder||'',
                cls:e.className||'', aria:e.getAttribute('aria-label')||''
            })"""
        )
        blob = " ".join(str(v) for v in meta.values()).lower()
        score = 0
        if "date" in blob: score += 10
        if "from" in blob or "start" in blob: score += 5
        if "to" in blob or "end" in blob: score += 5
        if meta["type"] in {"text", "date"}: score += 2
        if score:
            scored.append((score, i))
    scored.sort(reverse=True)
    if len(scored) >= 2:
        return [inputs.nth(i) for _, i in scored[:2]]
    generic = [
        inputs.nth(i) for i in range(inputs.count())
        if inputs.nth(i).get_attribute("type") in {"text", "date"}
    ]
    if len(generic) >= 2:
        return generic[-2:]
    raise RuntimeError(
        "Could not identify NSE date inputs. "
        f"Visible inputs: {_visible_input_inventory(page)!r}"
    )


def _choose_dates(page, start: dt.date, end: dt.date) -> None:
    fields = _find_date_inputs(page)
    fields[0].fill(start.strftime("%d/%m/%Y"))
    fields[0].press("Tab")
    fields[1].fill(end.strftime("%d/%m/%Y"))
    fields[1].press("Tab")


def _submit_return_form(page) -> None:
    buttons = page.locator("button:visible")
    matches = [
        buttons.nth(i)
        for i in range(buttons.count())
        if buttons.nth(i).inner_text().strip().lower() == "submit"
    ]
    if not matches:
        raise RuntimeError("No visible Submit button found on NSE return-data form.")
    matches[-1].click(force=True)


def _parse_visible_table(page, index_name: str, start: dt.date, end: dt.date) -> list[dict]:
    tables = page.locator("table:visible")
    for i in range(tables.count()):
        table = tables.nth(i)
        text = table.inner_text().upper()
        if "TOTAL RETURNS INDEX" not in text or "DATE" not in text:
            continue
        rows = table.locator("tbody tr")
        out = []
        for j in range(rows.count()):
            cells = [c.strip() for c in rows.nth(j).locator("td").all_inner_texts()]
            if len(cells) < 2:
                continue
            try:
                d = dt.datetime.strptime(cells[0], "%d %b %Y").date()
                tri = float(cells[1].replace(",", ""))
            except (ValueError, TypeError):
                continue
            if start <= d <= end:
                out.append({
                    "date": d.isoformat(),
                    "value": tri,
                    "source": "Nifty Indices Historical Data — Total Returns Index Values",
                    "source_reference": PAGE_URL,
                })
        if out:
            return out
    raise RuntimeError(
        f"No visible official TRI table for {index_name} {start} -> {end}. "
        f"Page excerpt: {page.locator('body').inner_text(timeout=10000)[:3000]!r}"
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "value", "source", "source_reference"]
    fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".csv", dir=str(path.parent))
    os.close(fd)
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=fields).writerows(rows)
        os.replace(tmp, path)
    finally:
        try: os.unlink(tmp)
        except OSError: pass


def fetch_with_ui(index_name: str, subindex: str, start: dt.date, end: dt.date) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Run: python -m pip install playwright") from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context(locale="en-US")
        page = context.new_page()
        try:
            print(f"Opening official NSE page: {PAGE_URL}")
            page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(6000)

            # The official page currently opens the "Total returns Index Values"
            # panel by default. Do not click the duplicate accordion label: NSE renders
            # a hidden copy of that text and a click can target the wrong node.
            # Drive the actual form controls shown in the live UI instead.
            page.locator(f"#{RETURN_TYPE_ID}").wait_for(state="visible", timeout=30000)
            page.locator(f"#{RETURN_SUBINDEX_ID}").wait_for(state="visible", timeout=30000)
            page.locator(f"#{RETURN_INDEX_ID}").wait_for(state="visible", timeout=30000)
            _select_by_text(page, f"#{RETURN_TYPE_ID}", "Equity")
            page.wait_for_timeout(1500)
            _select_by_text(page, f"#{RETURN_SUBINDEX_ID}", subindex)
            page.wait_for_timeout(1500)
            _select_by_text(page, f"#{RETURN_INDEX_ID}", index_name)
            page.wait_for_timeout(1000)

            _choose_dates(page, start, end)
            print(f"Submitting official UI: {index_name} | {start} -> {end}")
            _submit_return_form(page)
            page.wait_for_timeout(5000)
            return _parse_visible_table(page, index_name, start, end)
        finally:
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, help="Download one calendar year only.")
    args = parser.parse_args()

    years = [args.year] if args.year else list(range(START.year, END.year + 1))

    for index_name, (subindex, filename) in TARGETS.items():
        merged = {}
        for year in years:
            start = max(START, dt.date(year, 1, 1))
            end = min(END, dt.date(year, 12, 31))
            rows = fetch_with_ui(index_name, subindex, start, end)
            for row in rows:
                merged[row["date"]] = row
            print(f"{index_name} {year}: {len(rows)} observations")
        rows = [merged[k] for k in sorted(merged)]
        if not rows:
            raise RuntimeError(f"No official TRI observations obtained for {index_name}.")
        path = OUT_DIR / filename
        write_csv(path, rows)
        print(f"{index_name}: {len(rows)} observations | {rows[0]['date']} -> {rows[-1]['date']} | {path}")

    print("STATUS: PASS — official TRI values acquired through the NSE Historical Data UI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
