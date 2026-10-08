"""Canonical loader for NSE CM Bhavcopy legacy and 2024+ schemas.

This module deliberately leaves raw files untouched and normalizes only the
field names required by the V6 performance layer. It does not adjust prices.
"""
from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Mapping


@dataclass(frozen=True)
class PriceBar:
    date: date
    symbol: str
    series: str
    isin: str
    open: float
    high: float
    low: float
    close: float


OLD = {"SYMBOL": "symbol", "SERIES": "series", "ISIN": "isin",
       "OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close",
       "TIMESTAMP": "date"}
NEW = {"TckrSymb": "symbol", "SctySrs": "series", "ISIN": "isin",
       "OpnPric": "open", "HghPric": "high", "LwPric": "low",
       "ClsPric": "close", "TradDt": "date"}


def _parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y"):
        from datetime import datetime
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported NSE date: {value!r}")


def _read_csv_bytes(raw: bytes, path: Path) -> Dict[str, PriceBar]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    columns = set(reader.fieldnames or [])
    mapping = OLD if set(OLD).issubset(columns) else NEW if set(NEW).issubset(columns) else None
    if mapping is None:
        raise ValueError(f"unknown NSE price schema: {path}")
    out: Dict[str, PriceBar] = {}
    for row in reader:
        if (row.get(next(k for k,v in mapping.items() if v == "series")) or "").strip() != "EQ":
            continue
        symbol = (row.get(next(k for k,v in mapping.items() if v == "symbol")) or "").strip()
        if not symbol:
            continue
        try:
            bar = PriceBar(
                date=_parse_date(row[next(k for k,v in mapping.items() if v == "date")]),
                symbol=symbol,
                series="EQ",
                isin=(row.get(next(k for k,v in mapping.items() if v == "isin")) or "").strip(),
                open=float(row[next(k for k,v in mapping.items() if v == "open")]),
                high=float(row[next(k for k,v in mapping.items() if v == "high")]),
                low=float(row[next(k for k,v in mapping.items() if v == "low")]),
                close=float(row[next(k for k,v in mapping.items() if v == "close")]),
            )
        except (KeyError, TypeError, ValueError):
            continue
        if min(bar.open, bar.high, bar.low, bar.close) <= 0:
            continue
        out[symbol] = bar
    return out


def load_bhavcopy(path: Path) -> Mapping[str, PriceBar]:
    """Load one raw NSE Bhavcopy without price adjustment."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError(f"expected exactly one CSV in {path.name}, found {len(names)}")
            raw = archive.read(names[0])
    else:
        raw = path.read_bytes()
    return _read_csv_bytes(raw, path)


def load_raw_instrument_close_by_isin(
    path: Path,
    isin: str,
    expected_date: date,
) -> float:
    """Read one instrument's unadjusted close by ISIN, including non-EQ series.

    Unlike load_bhavcopy(), this deliberately does not filter to the equity
    series. It is intended for auditable corporate-action sensitivity inputs,
    not for equity execution prices.
    """
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError(
                    f"expected exactly one CSV in {path.name}, found {len(names)}"
                )
            raw = archive.read(names[0])
    else:
        raw = path.read_bytes()

    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    fields = set(reader.fieldnames or [])
    if {"ISIN", "CLOSE", "TIMESTAMP"}.issubset(fields):
        isin_col, close_col, date_col = "ISIN", "CLOSE", "TIMESTAMP"
    elif {"ISIN", "ClsPric", "TradDt"}.issubset(fields):
        isin_col, close_col, date_col = "ISIN", "ClsPric", "TradDt"
    else:
        raise ValueError(f"unknown NSE raw instrument-price schema: {path}")

    matches: list[float] = []
    for row in reader:
        if (row.get(isin_col) or "").strip().upper() != isin.strip().upper():
            continue
        try:
            row_date = _parse_date(row.get(date_col) or "")
            close = float(row.get(close_col) or "")
        except (TypeError, ValueError):
            continue
        if row_date == expected_date:
            if close <= 0:
                raise ValueError(
                    f"non-positive raw close for ISIN {isin} on {expected_date}"
                )
            matches.append(close)

    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one raw close for ISIN {isin} on {expected_date}; "
            f"found {len(matches)} in {path.name}"
        )
    return matches[0]


class ManifestPriceStore:
    """Lazy, deterministic price access backed by the repository manifest."""

    def __init__(self, root: Path, manifest_rows: list[dict[str, str]]):
        self.root = Path(root)
        self.manifest = {r["date"]: r for r in manifest_rows}
        self._cache: dict[date, Mapping[str, PriceBar]] = {}

    @classmethod
    def from_manifest(cls, root: Path, manifest: Path) -> "ManifestPriceStore":
        with manifest.open("r", encoding="utf-8-sig", newline="") as f:
            return cls(root, list(csv.DictReader(f)))

    def prices(self, trading_date: date) -> Mapping[str, PriceBar]:
        if trading_date in self._cache:
            return self._cache[trading_date]
        key = trading_date.isoformat()
        row = self.manifest.get(key)
        if row is None:
            raise KeyError(f"price manifest missing {key}")
        path = self.root / row["format"] / Path(row["url"]).name
        if not path.exists():
            raise FileNotFoundError(path)
        loaded = load_bhavcopy(path)
        self._cache[trading_date] = loaded
        return loaded
