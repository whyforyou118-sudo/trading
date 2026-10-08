"""Audit local NSE bhavcopy coverage for Britannia bonus debentures.

This is a source-coverage audit only, not a portfolio simulation. It scans the
already-downloaded raw bhavcopy files for the two known ISINs and reports raw
OHLC observations, first/last dates, and expected listing/redemption dates.
A redemption-date price row is diagnostic only: a redeemed security may no
longer appear in that day's market file. This audit does not value the debt
instruments or authorize Run 1.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = ROOT / "data" / "raw" / "prices"
MANIFEST = RAW_ROOT / "download_manifest.csv"
OUTPUT = ROOT / "audits" / "phase1b_britannia_debenture_price_audit.csv"

INSTRUMENTS = {
    "INE216A07052": {
        "name": "BRITANNIA_2019_8PCT_SECURED_BONUS_DEBENTURE",
        "listing_date": "2019-10-09",
        "redemption_date": "2022-08-26",
        "face_value": 30.0,
        "coupon_pct": 8.0,
    },
    "INE216A08027": {
        "name": "BRITANNIA_2021_5PCT5_UNSECURED_BONUS_DEBENTURE",
        "listing_date": "2021-07-20",
        "redemption_date": "2024-06-03",
        "face_value": 29.0,
        "coupon_pct": 5.5,
    },
}

OLD = {
    "symbol": "SYMBOL", "series": "SERIES", "date": "TIMESTAMP",
    "open": "OPEN", "high": "HIGH", "low": "LOW", "close": "CLOSE",
    "isin": "ISIN",
}
NEW = {
    "symbol": "TckrSymb", "series": "SctySrs", "date": "TradDt",
    "open": "OpnPric", "high": "HghPric", "low": "LwPric",
    "close": "ClsPric", "isin": "ISIN",
}


def _iso_date(value: str) -> str:
    value = (value or "").strip()
    if len(value) == 10 and value[4] == "-" and value[0:4].isdigit():
        return value
    for fmt in ("%d-%b-%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unsupported NSE date: {value!r}")


def parse_debenture_rows(raw: bytes, source_file: str = "<memory>") -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    fields = set(reader.fieldnames or [])
    if set(OLD.values()).issubset(fields):
        mapping = OLD
    elif set(NEW.values()).issubset(fields):
        mapping = NEW
    else:
        raise ValueError(f"unknown NSE bhavcopy schema in {source_file}")

    out: list[dict[str, str]] = []
    for row in reader:
        isin = (row.get(mapping["isin"]) or "").strip().upper()
        if isin not in INSTRUMENTS:
            continue
        item = {
            "date": _iso_date(row.get(mapping["date"]) or ""),
            "isin": isin,
            "instrument": INSTRUMENTS[isin]["name"],
            "symbol": (row.get(mapping["symbol"]) or "").strip().upper(),
            "series": (row.get(mapping["series"]) or "").strip().upper(),
            "open": (row.get(mapping["open"]) or "").strip(),
            "high": (row.get(mapping["high"]) or "").strip(),
            "low": (row.get(mapping["low"]) or "").strip(),
            "close": (row.get(mapping["close"]) or "").strip(),
            "source_file": source_file,
        }
        for key in ("open", "high", "low", "close"):
            try:
                value = float(item[key])
            except ValueError as exc:
                raise ValueError(f"invalid {key} for {isin} on {item['date']}") from exc
            if value <= 0:
                raise ValueError(f"non-positive {key} for {isin} on {item['date']}")
            item[key] = f"{value:.10g}"
        out.append(item)
    return out


def _read_manifest_file(path: Path) -> bytes:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError(f"expected exactly one CSV in {path}; found {len(names)}")
            return archive.read(names[0])
    return path.read_bytes()


def main() -> int:
    if not MANIFEST.exists():
        print(f"BLOCKED: missing local raw-price manifest: {MANIFEST}")
        return 2
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        manifest_rows = list(csv.DictReader(f))

    observations: list[dict[str, str]] = []
    failures: list[str] = []
    for row in manifest_rows:
        session_date = (row.get("date") or "").strip()
        if not session_date:
            failures.append("manifest row missing date")
            continue
        path = RAW_ROOT / (row.get("format") or "") / Path(row.get("url") or "").name
        if not path.exists():
            failures.append(f"raw file missing for {session_date}: {path}")
            continue
        try:
            observations.extend(parse_debenture_rows(_read_manifest_file(path), path.name))
        except Exception as exc:
            failures.append(f"{session_date}: {type(exc).__name__}: {exc}")

    counts = Counter((item["isin"], item["date"]) for item in observations)
    duplicates = [f"{isin} {d}: {count} rows" for (isin, d), count in counts.items() if count != 1]
    failures.extend(duplicates)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["date", "isin", "instrument", "symbol", "series",
                        "open", "high", "low", "close", "source_file"],
        )
        writer.writeheader()
        writer.writerows(sorted(observations, key=lambda x: (x["isin"], x["date"])))

    summaries = []
    for isin, spec in INSTRUMENTS.items():
        rows = sorted((x for x in observations if x["isin"] == isin), key=lambda x: x["date"])
        date_set = {x["date"] for x in rows}
        summaries.append({
            "isin": isin,
            "instrument": spec["name"],
            "observations": len(rows),
            "first_observed_date": rows[0]["date"] if rows else None,
            "last_observed_date": rows[-1]["date"] if rows else None,
            "listing_date_observed": spec["listing_date"] in date_set,
            "redemption_date_observed": spec["redemption_date"] in date_set,
            "listing_date": spec["listing_date"],
            "redemption_date": spec["redemption_date"],
        })
        if not rows:
            failures.append(f"no raw observations found for {isin}")
        if spec["listing_date"] not in date_set:
            failures.append(f"listing date {spec['listing_date']} absent for {isin}")

    report = {
        "audit_type": "BRITANNIA_DEBENTURE_RAW_PRICE_COVERAGE_NOT_PERFORMANCE",
        "manifest_rows": len(manifest_rows),
        "raw_observations": len(observations),
        "instrument_summaries": summaries,
        "failures": failures,
        "status": "PASS" if not failures else "BLOCKED",
        "performance_run_authorized": False,
        "output": str(OUTPUT.relative_to(ROOT)),
    }
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
