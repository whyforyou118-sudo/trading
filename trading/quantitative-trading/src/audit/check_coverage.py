import csv
import datetime
import io
import zipfile
from pathlib import Path

def infer_date(filename: str) -> str:
    name = Path(filename).name
    try:
        if name.startswith("cm") and "bhav.csv" in name:
            return datetime.datetime.strptime(name[2:11], "%d%b%Y").date().isoformat()
        if name.startswith("BhavCopy_NSE_CM_"):
            return datetime.datetime.strptime(name.split("_")[5], "%Y%m%d").date().isoformat()
    except (ValueError, IndexError):
        return ""
    return ""

def parse_csv_stream(stream, display_name: str):
    result = {"filename": display_name, "trading_date": infer_date(display_name),
              "row_count": 0, "unique_symbols": set(), "duplicate_rows": 0,
              "missing_ohlc": 0, "invalid_ohlc": 0, "negative_price": 0,
              "volume_anomalies": 0, "missing_isin": 0, "duplicate_symbol_isin": 0,
              "schema_consistency": "unknown", "error": ""}
    try:
        text = stream.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        cols = set(reader.fieldnames or [])
        if {"SYMBOL","SERIES","OPEN","HIGH","LOW","CLOSE","TOTTRDQTY","ISIN"}.issubset(cols):
            result["schema_consistency"] = "legacy"
            sym_key, series_key = "SYMBOL", "SERIES"
            open_key, high_key, low_key, close_key = "OPEN","HIGH","LOW","CLOSE"
            vol_key, isin_key = "TOTTRDQTY","ISIN"
        elif {"TckrSymb","SctySrs","OpnPric","HghPric","LwPric","ClsPric","TtlTradgVol","ISIN"}.issubset(cols):
            result["schema_consistency"] = "udiff"
            sym_key, series_key = "TckrSymb", "SctySrs"
            open_key, high_key, low_key, close_key = "OpnPric","HghPric","LwPric","ClsPric"
            vol_key, isin_key = "TtlTradgVol","ISIN"
        else:
            result["error"] = "unknown schema"
            return result
        seen_rows, seen_symbol_isin = set(), set()
        for row in reader:
            result["row_count"] += 1
            sym, ser = (row.get(sym_key) or "").strip(), (row.get(series_key) or "").strip()
            result["unique_symbols"].add(sym)
            key = (sym, ser)
            if key in seen_rows: result["duplicate_rows"] += 1
            seen_rows.add(key)
            try:
                o,h,l,c = [float(row.get(k) or 0) for k in (open_key,high_key,low_key,close_key)]
            except (TypeError, ValueError):
                result["missing_ohlc"] += 1
                continue
            if not (l <= o <= h and l <= c <= h): result["invalid_ohlc"] += 1
            if min(o,h,l,c) <= 0: result["negative_price"] += 1
            try:
                if float(row.get(vol_key) or 0) > 5e8: result["volume_anomalies"] += 1
            except (TypeError, ValueError):
                result["volume_anomalies"] += 1
            isin = (row.get(isin_key) or "").strip()
            if not isin: result["missing_isin"] += 1
            else:
                pair = (sym, isin)
                if pair in seen_symbol_isin: result["duplicate_symbol_isin"] += 1
                seen_symbol_isin.add(pair)
    except Exception as exc:
        result["error"] = str(exc)
    return result

def parse_price_file(filepath: Path):
    if filepath.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                if len(members) != 1:
                    return {"filename": str(filepath), "trading_date": infer_date(filepath.name),
                            "row_count": 0, "unique_symbols": set(), "duplicate_rows": 0,
                            "missing_ohlc": 0, "invalid_ohlc": 0, "negative_price": 0,
                            "volume_anomalies": 0, "missing_isin": 0, "duplicate_symbol_isin": 0,
                            "schema_consistency": "unknown", "error": "expected exactly one CSV in ZIP"}
                with zf.open(members[0], "r") as stream:
                    return parse_csv_stream(stream, str(filepath))
        except zipfile.BadZipFile as exc:
            return {"filename": str(filepath), "trading_date": infer_date(filepath.name),
                    "row_count": 0, "unique_symbols": set(), "duplicate_rows": 0,
                    "missing_ohlc": 0, "invalid_ohlc": 0, "negative_price": 0,
                    "volume_anomalies": 0, "missing_isin": 0, "duplicate_symbol_isin": 0,
                    "schema_consistency": "unknown", "error": f"invalid ZIP: {exc}"}
    with filepath.open("rb") as stream:
        return parse_csv_stream(stream, str(filepath))

def main():
    root = Path("data/raw/prices")
    out_csv, out_md = Path("audits/full_price_coverage.csv"), Path("audits/full_price_coverage.md")
    fields = ["filename","trading_date","row_count","unique_symbols","duplicate_rows","missing_ohlc",
              "invalid_ohlc","negative_price","volume_anomalies","missing_isin","duplicate_symbol_isin",
              "schema_consistency","error"]
    paths = sorted(list(root.rglob("*.zip")) + list(root.rglob("*.csv")))
    rows = [parse_price_file(p) for p in paths]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in rows:
            x = dict(r); x["unique_symbols"] = ";".join(sorted(r["unique_symbols"])); w.writerow(x)
    dates = [r["trading_date"] for r in rows if r["trading_date"]]
    symbols = set().union(*(r["unique_symbols"] for r in rows)) if rows else set()
    failed = sum(bool(r["error"]) for r in rows)
    suspicious = sum(any(r[k] for k in ["duplicate_rows","missing_ohlc","invalid_ohlc","negative_price",
                                          "volume_anomalies","missing_isin","duplicate_symbol_isin"]) for r in rows)
    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Full Price Coverage Audit\n\n")
        f.write(f"**Files checked:** {len(rows)}\n**Total rows:** {sum(r['row_count'] for r in rows)}\n")
        f.write(f"**Date range:** {min(dates) if dates else ''} – {max(dates) if dates else ''}\n")
        f.write(f"**Unique symbols:** {len(symbols)}\n**Failed files:** {failed}\n**Suspicious files:** {suspicious}\n")

if __name__ == "__main__":
    main()
