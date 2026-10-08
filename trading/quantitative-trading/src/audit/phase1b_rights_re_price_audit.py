"""Extract raw NSE bhavcopy opens for the two V6 rights-entitlement sales.

Reads only already-downloaded source files listed in data/raw/prices/download_manifest.csv.
It does not fetch prices, infer missing opens, or run portfolio performance.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = ROOT / "data" / "raw" / "prices"
MANIFEST = RAW_ROOT / "download_manifest.csv"
OUTPUT = ROOT / "audits" / "phase1b_rights_re_price_audit.csv"

TARGETS = {
    ("2024-01-17", "GRASIM-RE"),
    ("2024-08-05", "TATACON-RE"),
}
OLD = {
    "symbol": "SYMBOL", "series": "SERIES", "open": "OPEN",
    "date": "TIMESTAMP",
}
NEW = {
    "symbol": "TckrSymb", "series": "SctySrs", "open": "OpnPric",
    "date": "TradDt",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError(f"expected exactly one CSV in {path}; found {len(names)}")
            raw = archive.read(names[0])
    else:
        raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    fields = set(reader.fieldnames or [])
    if set(OLD.values()).issubset(fields):
        mapping = OLD
    elif set(NEW.values()).issubset(fields):
        mapping = NEW
    else:
        raise ValueError(f"unknown NSE schema in {path}")
    out = []
    for row in reader:
        symbol = (row.get(mapping["symbol"]) or "").strip().upper()
        if symbol not in {s for _, s in TARGETS}:
            continue
        date_text = (row.get(mapping["date"]) or "").strip()
        if "-" in date_text and len(date_text) == 10 and date_text[:4].isdigit():
            iso_date = date_text
        else:
            from datetime import datetime
            iso_date = None
            for fmt in ("%d-%b-%Y", "%d-%m-%Y"):
                try:
                    iso_date = datetime.strptime(date_text, fmt).date().isoformat()
                    break
                except ValueError:
                    pass
            if iso_date is None:
                raise ValueError(f"unsupported date {date_text!r} in {path}")
        if (iso_date, symbol) not in TARGETS:
            continue
        series = (row.get(mapping["series"]) or "").strip().upper()
        open_text = (row.get(mapping["open"]) or "").strip()
        out.append({
            "date": iso_date,
            "symbol": symbol,
            "series": series,
            "open": open_text,
            "source_file": path.name,
        })
    return out


def main() -> int:
    if not MANIFEST.exists():
        print(f"BLOCKED: missing local raw-price manifest: {MANIFEST}")
        return 2
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        manifest_rows = list(csv.DictReader(f))

    found: list[dict[str, str]] = []
    failures: list[str] = []
    for target_date, symbol in sorted(TARGETS):
        row = next((r for r in manifest_rows if r.get("date") == target_date), None)
        if row is None:
            failures.append(f"manifest missing session {target_date} for {symbol}")
            continue
        path = RAW_ROOT / row["format"] / Path(row["url"]).name
        if not path.exists():
            failures.append(f"raw file missing: {path}")
            continue
        matches = [
            item for item in read_rows(path)
            if item["date"] == target_date and item["symbol"] == symbol
        ]
        if len(matches) != 1:
            failures.append(
                f"expected exactly one raw row for {symbol} on {target_date}; "
                f"found {len(matches)}"
            )
            continue
        item = matches[0]
        try:
            open_price = float(item["open"])
        except ValueError:
            failures.append(f"invalid open for {symbol} on {target_date}: {item['open']!r}")
            continue
        if open_price <= 0:
            failures.append(f"non-positive open for {symbol} on {target_date}: {open_price}")
            continue
        item["open"] = f"{open_price:.10g}"
        found.append(item)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "symbol", "series", "open", "source_file"]
        )
        writer.writeheader()
        writer.writerows(found)

    report = {
        "audit_type": "RAW_RIGHTS_ENTITLEMENT_OPEN_SOURCE_CHECK_NOT_PERFORMANCE",
        "targets": len(TARGETS),
        "found_unique_rows": len(found),
        "failures": failures,
        "status": "PASS" if not failures and len(found) == len(TARGETS) else "BLOCKED",
        "performance_run_authorized": False,
        "output": str(OUTPUT.relative_to(ROOT)),
    }
    print(json.dumps(report, indent=2))
    if found:
        for item in found:
            print(
                f"PRICE: {item['date']} {item['symbol']} "
                f"series={item['series']} raw_open={item['open']}"
            )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
