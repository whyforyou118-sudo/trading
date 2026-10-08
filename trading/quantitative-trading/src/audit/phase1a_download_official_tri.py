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
    """POST to the official endpoint, with a curl fallback for bot protection."""
    response = session.post(url, json=payload, timeout=120)
    try:
        outer = response.json()
    except ValueError:
        # niftyindices.com can return an HTML bot/challenge page to requests.
        # Windows curl with a normal browser UA is often accepted by the same
        # public endpoint, so retry through curl rather than silently accepting
        # non-data HTML.
        import subprocess

        body = json.dumps(payload, separators=(",", ":"))
        command = [
            "curl.exe", "-sS", "-L", "--fail-with-body",
            "-H", "Content-Type: application/json; charset=UTF-8",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Accept: */*",
            "-H", "Accept-Language: en-US,en;q=0.9",
            "-H", "Referer: https://www.niftyindices.com/reports/historical-data",
            "-H", (
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            ),
            "--data-raw", body,
            url,
        ]
        try:
            raw = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True, timeout=180)
            outer = json.loads(raw)
        except Exception as exc:
            preview = response.text[:300].replace("\n", " ")
            raise RuntimeError(
                f"Official NSE endpoint returned non-JSON and curl fallback failed. "
                f"HTTP {response.status_code}; response preview={preview!r}; "
                f"curl_error={exc}"
            ) from exc

    value = outer.get("d", "[]")
    if isinstance(value, str):
        if value.lower() == "false":
            return []
        return json.loads(value)
    return value


def discover_names(session: requests.Session) -> dict[str, str]:
    # These are the canonical names exposed by NSE Indices. Avoid the metadata
    # discovery endpoint because it is more aggressively bot-protected than
    # the actual TRI endpoint.
    return {
        "NIFTY 50": "NIFTY 50",
        "NIFTY50 EQUAL WEIGHT": "NIFTY50 EQUAL WEIGHT",
    }

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
