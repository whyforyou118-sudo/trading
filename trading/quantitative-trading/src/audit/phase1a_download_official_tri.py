"""Download official NSE Indices gross TRI benchmarks for Phase 1A.

Uses the public niftyindices.com historical-data API. The API's canonical
index names are discovered from its Equity/TRI metadata endpoint, then the
two frozen benchmark series are fetched in <=365-day chunks.
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
    response = session.post(url, json=payload, timeout=60)
    response.raise_for_status()
    value = response.json().get("d", "[]")
    if isinstance(value, str):
        if value.lower() == "false":
            return []
        return json.loads(value)
    return value


def discover_names(session: requests.Session) -> dict[str, str]:
    """Discover canonical TRI names from the official dropdown metadata."""
    categories = post_json(
        session,
        SUBTYPE_URL,
        {"cinfo": {"indextype": "Equity", "indexgroup": "Total Returns Index Values"}},
    )

    discovered: set[str] = set()
    for row in categories:
        category = str(row.get("indextype", "")).strip()
        if not category:
            continue
        rows = post_json(
            session,
            INDEXDATA_URL,
            {"cinfo": {"indextype": category, "indexgroup": "Total Returns Index Values"}},
        )
        for item in rows:
            name = str(item.get("indextype", "")).strip()
            if name:
                discovered.add(name.upper())

    resolved: dict[str, str] = {}
    for target in TARGETS:
        exact = next((x for x in discovered if x == target), None)
        if exact is None:
            raise RuntimeError(
                f"Official TRI metadata did not expose {target!r}. "
                f"Available matching names: "
                f"{sorted(x for x in discovered if 'NIFTY' in x)[:100]}"
            )
        resolved[target] = exact
    return resolved


def fetch_tri(session: requests.Session, index_name: str) -> list[dict]:
    rows: list[dict] = []
    cursor = START

    while cursor <= END:
        chunk_end = min(cursor + timedelta(days=364), END)
        inner = (
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
        chunk = post_json(session, TRI_URL, {"cinfo": inner})
        if not chunk:
            raise RuntimeError(
                f"No TRI rows returned for {index_name}: {cursor} to {chunk_end}"
            )
        rows.extend(chunk)
        cursor = chunk_end + timedelta(days=1)

    values: dict[str, float] = {}
    for row in rows:
        raw_date = row.get("Date")
        raw_tri = row.get("TotalReturnsIndex")
        if raw_date is None or raw_tri in (None, ""):
            continue
        dt = datetime.strptime(str(raw_date), "%d %b %Y").date()
        if START <= dt <= END:
            values[dt.isoformat()] = float(raw_tri)

    ordered = [{"date": d, "tri": values[d]} for d in sorted(values)]
    if not ordered:
        raise RuntimeError(f"No usable TRI observations for {index_name}")
    return ordered


def write_csv(path: Path, rows: list[dict], index_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("index_name,date,tri\n")
        for row in rows:
            handle.write(f"{index_name},{row['date']},{row['tri']:.8f}\n")


def main() -> None:
    session = requests.Session()
    session.headers.update(
        {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE,
            "Referer": f"{BASE}/reports/historical-data",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            ),
        }
    )

    # Prime the official page for Akamai/session compatibility. Failure here
    # is non-fatal because the API can operate without cookies.
    try:
        session.get(f"{BASE}/reports/historical-data", timeout=10)
    except requests.RequestException:
        pass

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
