"""Download official NSE Indices gross TRI benchmarks for Phase 1A.

Source: https://www.niftyindices.com/reports/historical-data
Endpoint: /Backpage.aspx/getTotalReturnIndexString

The endpoint limits requests to roughly one year, so the downloader uses
calendar-year chunks and validates the resulting daily series.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

BASE = "https://www.niftyindices.com"
MAPPING_URL = "https://iislliveblob.niftyindices.com/assets/json/IndexMapping.json"
TRI_URL = f"{BASE}/Backpage.aspx/getTotalReturnIndexString"
SUBTYPE_URL = f"{BASE}/Backpage.aspx/gethistoricaltypeSubindexdata"
INDEXDATA_URL = f"{BASE}/Backpage.aspx/gethistoricaltypeindexdata"

START = date(2018, 1, 1)
END = date(2025, 12, 31)
OUT_DIR = Path("data/reference")

TARGETS = {
    "NIFTY 50": "nifty50_tri.csv",
    "NIFTY50 EQUAL WEIGHT": "nifty50_equal_weight_tri.csv",
}


def post_json(session: requests.Session, url: str, payload: dict) -> object:
    r = session.post(url, json=payload, timeout=60)
    r.raise_for_status()
    outer = r.json()
    inner = outer.get("d", "[]")
    if isinstance(inner, str):
        if inner.lower() == "false":
            return []
        return json.loads(inner)
    return inner


def discover_names(session: requests.Session) -> dict[str, str]:
    mapping = session.get(MAPPING_URL, timeout=60)
    mapping.raise_for_status()
    mapping_rows = mapping.json()
    long_names = {
        str(x.get("Index_long_name", "")).strip().upper()
        for x in mapping_rows
        if x.get("Index_long_name")
    }

    discovered: set[str] = set()
    for subtype in ("Broad Market Indices", "Strategy Indices"):
        rows = post_json(
            session,
            INDEXDATA_URL,
            {"cinfo": {"indextype": subtype, "indexgroup": "Total Returns Index Values"}},
        )
        for row in rows:
            name = str(row.get("indextype", "")).strip()
            if name:
                discovered.add(name.upper())

    resolved = {}
    for target in TARGETS:
        exact = next((x for x in discovered if x == target), None)
        if exact is None:
            # Some site layers expose spacing/casing variants.
            exact = next(
                (x for x in discovered if x.replace(" ", "") == target.replace(" ", "")),
                None,
            )
        if exact is None:
            raise RuntimeError(
                f"Could not discover official TRI index name for {target}. "
                f"Available matches: {sorted(x for x in discovered if 'NIFTY50' in x.replace(' ', ''))}"
            )
        # Use the discovered display name for both fields. The mapping is retained
        # as a sanity check that the index is an official Nifty Indices name.
        if exact not in long_names and target == "NIFTY 50":
            raise RuntimeError("NIFTY 50 missing from official IndexMapping.json")
        resolved[target] = exact
    return resolved


def fetch_tri(session: requests.Session, index_name: str) -> list[dict]:
    rows: list[dict] = []
    cursor = START
    while cursor <= END:
        chunk_end = min(cursor + timedelta(days=364), END)
        payload = {
            "cinfo": (
                "{'name':'"
                + index_name
                + "','startDate':'"
                + cursor.strftime("%d %b %Y")
                + "','endDate':'"
                + chunk_end.strftime("%d %b %Y")
                + "','indexName':'"
                + index_name
                + "'}"
            )
        }
        chunk = post_json(session, TRI_URL, payload)
        if not chunk:
            raise RuntimeError(
                f"No TRI rows returned for {index_name}: {cursor} to {chunk_end}"
            )
        rows.extend(chunk)
        cursor = chunk_end + timedelta(days=1)

    clean = {}
    for row in rows:
        raw_date = row.get("Date") or row.get("HistoricalDate")
        raw_tri = row.get("TotalReturnsIndex")
        if raw_date is None or raw_tri in (None, ""):
            continue
        dt = datetime.strptime(str(raw_date), "%d %b %Y").date()
        if START <= dt <= END:
            clean[dt.isoformat()] = float(raw_tri)

    if not clean:
        raise RuntimeError(f"No usable TRI observations for {index_name}")

    ordered = [{"date": k, "tri": clean[k]} for k in sorted(clean)]
    return ordered


def write_csv(path: Path, rows: list[dict], index_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("index_name,date,tri\\n")
        for row in rows:
            f.write(f"{index_name},{row['date']},{row['tri']:.8f}\\n")


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": BASE,
            "Referer": f"{BASE}/reports/historical-data",
            "User-Agent": "Mozilla/5.0",
        }
    )

    resolved = discover_names(session)
    print("Official TRI names:")
    for target, actual in resolved.items():
        print(f"  {target} -> {actual}")

    for target, filename in TARGETS.items():
        rows = fetch_tri(session, resolved[target])
        path = OUT_DIR / filename
        write_csv(path, rows, resolved[target])
        print(
            f"{target}: {len(rows)} observations | "
            f"{rows[0]['date']} -> {rows[-1]['date']} | {path}"
        )

    print("STATUS: PASS — official gross TRI artifacts downloaded.")


if __name__ == "__main__":
    main()
