"""Download official Nifty50 Equal Weight Total Return Index (TRI).

The benchmark is the official NSE Indices Nifty50 Equal Weight TR index.
It is NOT reconstructed from constituent prices. This preserves the official
index's quarterly equal-weight alignment, semi-annual composition changes,
dividend treatment, and corporate-action methodology.
"""
from __future__ import annotations

import argparse, csv, datetime, json, os, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/reference/nifty50_equal_weight_tri.csv"
FIELDS = ["date", "value", "source", "source_reference"]
TRI_URL = "https://www.niftyindices.com/Backpage/getTotalReturnIndexString"
TRI_REFERER = "https://www.niftyindices.com/reports/historical-data"
TRI_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)
INDEX_NAME = "Nifty50 Equal Weight"


def make_session():
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError(
            "httpx is required. Install with: python -m pip install httpx"
        ) from exc
    return httpx.Client(
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": TRI_REFERER,
            "User-Agent": TRI_UA,
        },
        follow_redirects=True,
        timeout=120.0,
    )


def request_chunk(session, start, end):
    parameters = {
        "name": INDEX_NAME,
        "startDate": start.strftime("%d-%b-%Y"),
        "endDate": end.strftime("%d-%b-%Y"),
        "indexName": INDEX_NAME,
    }
    payload = {"cinfo": json.dumps(parameters)}
    response = session.post(TRI_URL, content=json.dumps(payload))
    if response.status_code != 200:
        raise RuntimeError(
            f"Nifty Indices Equal Weight TRI HTTP {response.status_code}: "
            f"{response.text[:500]!r}"
        )

    raw = response.text.lstrip("\ufeff").strip()
    if not raw or raw[:1] not in "{[":
        raise RuntimeError(
            f"Nifty Indices Equal Weight TRI returned non-JSON content: "
            f"content_type={response.headers.get('content-type')!r}; "
            f"body={raw[:500]!r}"
        )

    obj = json.loads(raw)
    if isinstance(obj, dict):
        raw_rows = obj.get("d", obj)
    elif isinstance(obj, list):
        raw_rows = obj
    else:
        raise RuntimeError(f"Unexpected JSON root: {type(obj).__name__}")

    if isinstance(raw_rows, str):
        raw_rows = json.loads(raw_rows)
    if not isinstance(raw_rows, list):
        raise RuntimeError(
            f"Unexpected TRI record payload: {type(raw_rows).__name__}"
        )

    rows = []
    for item in raw_rows:
        date_text = item.get("Date") or item.get("HistoricalDate")
        value = item.get("TotalReturnsIndex")
        if not date_text or value in (None, ""):
            continue
        d = datetime.datetime.strptime(date_text, "%d %b %Y").date()
        rows.append(
            {
                "date": d.isoformat(),
                "value": float(value),
                "source": "Nifty Indices Historical Data — Total Returns Index Values",
                "source_reference": "https://www.niftyindices.com/reports/historical-data",
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default="2025-12-31")
    args = parser.parse_args()

    start = datetime.date.fromisoformat(args.start)
    end = datetime.date.fromisoformat(args.end)
    if end < start:
        raise SystemExit("end must be >= start")

    all_rows = {}
    with make_session() as session:
        current = start
        while current <= end:
            chunk_end = min(current + datetime.timedelta(days=364), end)
            print(f"Downloading official Equal Weight TRI: {current} -> {chunk_end}")
            for row in request_chunk(session, current, chunk_end):
                all_rows[row["date"]] = row
            current = chunk_end + datetime.timedelta(days=1)

    rows = [all_rows[k] for k in sorted(all_rows)]
    if not rows:
        raise SystemExit("No Equal Weight TRI observations returned")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix="nifty50_equal_weight_tri.", suffix=".csv", dir=str(OUT.parent)
    )
    os.close(fd)
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, OUT)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    print(f"Wrote {len(rows)} observations: {OUT}")
    print(f"Coverage: {rows[0]['date']} -> {rows[-1]['date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
