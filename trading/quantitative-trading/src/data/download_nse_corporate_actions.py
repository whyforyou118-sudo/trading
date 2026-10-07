"""Download NSE equity corporate actions for the frozen V6 research period.

Source: NSE India Corporate Actions endpoint used by the public Corporate Actions
page. This script is a transport/archival layer only; it does not invent
adjustment factors or convert events into returns.

The downloader:
- queries the official NSE endpoint in <=365-day chunks;
- stores each raw JSON response unchanged;
- records SHA-256 hashes and HTTP metadata;
- writes a normalized combined CSV without dropping source fields;
- deduplicates only exact duplicate records;
- fails closed on HTTP/schema errors.

Run from the repository root.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "data" / "raw" / "corporate_actions"
RAW_ROOT = OUT_ROOT / "nse_api_raw"
MANIFEST = OUT_ROOT / "nse_corporate_actions_download_manifest.csv"
NORMALIZED = OUT_ROOT / "nse_corporate_actions_2018_2025.csv"

API_URL = "https://www.nseindia.com/api/corporates-corporateactions"
ORIGIN_URL = "https://www.nseindia.com/companies-listing/corporate-filings-actions"
MAX_CHUNK_DAYS = 365
FIELDS = [
    "chunk_start",
    "chunk_end",
    "http_status",
    "record_count",
    "sha256",
    "raw_file",
    "download_timestamp",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def daterange_chunks(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        chunk_end = min(cur + dt.timedelta(days=MAX_CHUNK_DAYS - 1), end)
        yield cur, chunk_end
        cur = chunk_end + dt.timedelta(days=1)


def request_chunk(session: requests.Session, start: dt.date, end: dt.date) -> tuple[bytes, list[dict[str, Any]]]:
    params = {
        "index": "equities",
        "from_date": start.strftime("%d-%m-%Y"),
        "to_date": end.strftime("%d-%m-%Y"),
    }
    response = session.get(
        API_URL,
        params=params,
        headers={"Referer": ORIGIN_URL},
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"NSE corporate-actions request failed: HTTP {response.status_code} "
            f"for {start}..{end}: {response.text[:300]}"
        )

    payload = response.content
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"NSE returned non-JSON content for {start}..{end}"
        ) from exc

    if not isinstance(data, list):
        raise RuntimeError(
            f"Unexpected NSE corporate-actions schema for {start}..{end}: "
            f"{type(data).__name__}"
        )

    records: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            raise RuntimeError(
                f"Unexpected corporate-action record type: {type(item).__name__}"
            )
        records.append(item)

    return payload, records


def write_manifest(rows: list[dict[str, Any]]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(MANIFEST)


def write_normalized(records: list[dict[str, Any]]) -> None:
    NORMALIZED.parent.mkdir(parents=True, exist_ok=True)

    # Preserve every source field encountered. Empty cells are used only when
    # a field is absent from an individual source record.
    field_names = sorted({key for row in records for key in row})
    if not field_names:
        raise RuntimeError("NSE returned zero source fields across all chunks")

    tmp = NORMALIZED.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow({key: row.get(key, "") for key in field_names})
    tmp.replace(NORMALIZED)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--sleep", type=float, default=1.0)
    args = parser.parse_args()

    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    if start > end:
        raise SystemExit("--start must be <= --end")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
    })

    # Warm the NSE session before calling the API endpoint.
    warm = session.get(ORIGIN_URL, timeout=60)
    if warm.status_code >= 400:
        raise RuntimeError(f"NSE landing page failed: HTTP {warm.status_code}")

    manifest_rows: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    seen: set[str] = set()

    chunks = list(daterange_chunks(start, end))
    print(f"NSE corporate-action chunks: {len(chunks)}")

    for idx, (chunk_start, chunk_end) in enumerate(chunks, 1):
        payload, records = request_chunk(session, chunk_start, chunk_end)
        digest = sha256_bytes(payload)
        raw_name = f"corporate_actions_{chunk_start:%Y%m%d}_{chunk_end:%Y%m%d}.json"
        raw_path = RAW_ROOT / raw_name
        raw_path.write_bytes(payload)

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        manifest_rows.append({
            "chunk_start": chunk_start.isoformat(),
            "chunk_end": chunk_end.isoformat(),
            "http_status": 200,
            "record_count": len(records),
            "sha256": digest,
            "raw_file": str(raw_path.relative_to(ROOT)),
            "download_timestamp": now,
        })

        for record in records:
            # Exact-record deduplication only. No semantic merging occurs here.
            key = json.dumps(record, sort_keys=True, separators=(",", ":"))
            if key not in seen:
                seen.add(key)
                all_records.append(record)

        print(
            f"{idx}/{len(chunks)}: {chunk_start}..{chunk_end} "
            f"records={len(records)} unique_total={len(all_records)}"
        )
        write_manifest(manifest_rows)
        time.sleep(args.sleep)

    if not all_records:
        raise RuntimeError("NSE returned no corporate actions for the requested period")

    write_normalized(all_records)

    print("NSE CORPORATE-ACTION DOWNLOAD")
    print(f"Period: {start} -> {end}")
    print(f"Chunks: {len(chunks)}")
    print(f"Unique exact records: {len(all_records)}")
    print(f"Manifest: {MANIFEST}")
    print(f"Normalized source: {NORMALIZED}")
    print("STATUS: PASS — raw NSE responses archived and hashed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
