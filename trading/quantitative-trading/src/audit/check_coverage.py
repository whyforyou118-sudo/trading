import csv, os, datetime
from pathlib import Path

def parse_price_file(filepath: Path):
    """Parse a bhavcopy CSV (legacy or UDiFF) and return a dict of metrics.
    Returns a dict with keys matching the full_price_coverage columns.
    """
    result = {
        'filename': str(filepath),
        'trading_date': '',
        'row_count': 0,
        'unique_symbols': [],
        'duplicate_rows': 0,
        'missing_ohlc': 0,
        'invalid_ohlc': 0,
        'negative_price': 0,
        'volume_anomalies': 0,
        'missing_isin': 0,
        'duplicate_symbol_isin': 0,
        'date_consistency': 'OK',
        'schema_consistency': 'unknown',
        'error': ''
    }
    try:
        with filepath.open('r', newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            # Detect schema
            if {'SYMBOL','SERIES','OPEN','HIGH','LOW','CLOSE','TOTTRDQTY','TOTTRDVAL','ISIN'}.issubset(cols):
                result['schema_consistency'] = 'legacy'
                sym_key, series_key = 'SYMBOL', 'SERIES'
                open_key, high_key, low_key, close_key = 'OPEN','HIGH','LOW','CLOSE'
                vol_key, isin_key = 'TOTTRDQTY','ISIN'
            elif {'TckrSymb','SctySrs','OpnPric','HghPric','LwPric','ClsPric','TtlTradgVol','TtlTrfVal','ISIN'}.issubset(cols):
                result['schema_consistency'] = 'udiff'
                sym_key, series_key = 'TckrSymb', 'SctySrs'
                open_key, high_key, low_key, close_key = 'OpnPric','HghPric','LwPric','ClsPric'
                vol_key, isin_key = 'TtlTradgVol','ISIN'
            else:
                result['schema_consistency'] = 'unknown'
                # fallback generic keys
                sym_key = next((k for k in ['SYMBOL','TckrSymb'] if k in cols), None)
                series_key = next((k for k in ['SERIES','SctySrs'] if k in cols), None)
                open_key = next((k for k in ['OPEN','OpnPric'] if k in cols), None)
                high_key = next((k for k in ['HIGH','HghPric'] if k in cols), None)
                low_key = next((k for k in ['LOW','LwPric'] if k in cols), None)
                close_key = next((k for k in ['CLOSE','ClsPric'] if k in cols), None)
                vol_key = next((k for k in ['TOTTRDQTY','TtlTradgVol'] if k in cols), None)
                isin_key = 'ISIN' if 'ISIN' in cols else None

            seen_rows = set()
            seen_symbol_isin = set()
            symbols = set()
            for row in reader:
                result['row_count'] += 1
                # trading date from filename if not already set
                if not result['trading_date']:
                    # Try to infer date from filename patterns
                    name = filepath.name
                    # legacy: cmDDMMMYYYYbhav.csv.zip -> extract DDMMMYYYY
                    # udiff: BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip
                    try:
                        if result['schema_consistency'] == 'legacy':
                            dt_str = name[2:9]  # e.g., 01JAN17 -> need to parse
                            dt = datetime.datetime.strptime(dt_str, '%d%b%Y').date()
                        else:
                            dt_str = name.split('_')[-3]  # YYYYMMDD
                            dt = datetime.datetime.strptime(dt_str, '%Y%m%d').date()
                        result['trading_date'] = dt.isoformat()
                    except Exception:
                        pass
                # symbol & series
                sym = row.get(sym_key, '').strip() if sym_key else ''
                ser = row.get(series_key, '').strip() if series_key else ''
                symbols.add(sym)
                # duplicate rows detection (symbol+series)
                key = (sym, ser)
                if key in seen_rows:
                    result['duplicate_rows'] += 1
                else:
                    seen_rows.add(key)
                # OHLC checks
                try:
                    o = float(row.get(open_key, 0) or 0)
                    h = float(row.get(high_key, 0) or 0)
                    l = float(row.get(low_key, 0) or 0)
                    c = float(row.get(close_key, 0) or 0)
                except Exception:
                    result['missing_ohlc'] += 1
                    continue
                if not (l <= o <= h and l <= c <= h):
                    result['invalid_ohlc'] += 1
                if o <= 0 or h <= 0 or l <= 0 or c <= 0:
                    result['negative_price'] += 1
                # volume
                try:
                    vol = float(row.get(vol_key, 0) or 0)
                    if vol > 5e8:
                        result['volume_anomalies'] += 1
                except Exception:
                    pass
                # ISIN
                if isin_key:
                    isin = row.get(isin_key, '').strip()
                    if not isin:
                        result['missing_isin'] += 1
                    else:
                        sym_isin = (sym, isin)
                        if sym_isin in seen_symbol_isin:
                            result['duplicate_symbol_isin'] += 1
                        else:
                            seen_symbol_isin.add(sym_isin)
            result['unique_symbols'] = list(sorted(symbols))
    except Exception as e:
        result['error'] = str(e)
    return result

def main():
    root = Path('data/raw/prices')
    out_csv = Path('audits/full_price_coverage.csv')
    out_md = Path('audits/full_price_coverage.md')
    fieldnames = ['filename','trading_date','row_count','unique_symbols','duplicate_rows','missing_ohlc','invalid_ohlc','negative_price','volume_anomalies','missing_isin','duplicate_symbol_isin','date_consistency','schema_consistency','error']
    rows = []
    for path in root.rglob('*.csv'):
        rows.append(parse_price_file(path))
    # write CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            # json-serialize list of symbols for CSV readability
            r_copy = r.copy()
            r_copy['unique_symbols'] = ';'.join(r_copy['unique_symbols'])
            writer.writerow(r_copy)
    # write markdown summary
    total_files = len(rows)
    total_rows = sum(r['row_count'] for r in rows)
    dates = [r['trading_date'] for r in rows if r['trading_date']]
    earliest = min(dates) if dates else ''
    latest = max(dates) if dates else ''
    uniq_symbols = set()
    for r in rows:
        uniq_symbols.update(r['unique_symbols'])
    failed = sum(1 for r in rows if r['error'])
    suspicious = sum(1 for r in rows if any([
        r['duplicate_rows'], r['missing_ohlc'], r['invalid_ohlc'], r['negative_price'], r['volume_anomalies'], r['missing_isin'], r['duplicate_symbol_isin']]))
    with out_md.open('w', encoding='utf-8') as f:
        f.write('# Full Price Coverage Audit (recursive)\n\n')
        f.write(f'**Total files:** {total_files}\n')
        f.write(f'**Total rows:** {total_rows}\n')
        f.write(f'**Date range:** {earliest} – {latest}\n')
        f.write(f'**Unique securities (across all files):** {len(uniq_symbols)}\n')
        f.write(f'**Failed files:** {failed}\n')
        f.write(f'**Suspicious files:** {suspicious}\n')
        f.write('\n')
        f.write('Sample of processed rows (first 5):\n')
        f.write('```csv\n')
        import io
        sio = io.StringIO()
        w = csv.DictWriter(sio, fieldnames=fieldnames)
        w.writeheader()
        for r in rows[:5]:
            rcopy = r.copy()
            rcopy['unique_symbols'] = ';'.join(rcopy['unique_symbols'])
            w.writerow(rcopy)
        f.write(sio.getvalue())
        f.write('```\n')

if __name__ == '__main__':
    main()
