import argparse, csv, datetime, hashlib, os, time, urllib.request, urllib.error
from pathlib import Path
import pandas_market_calendars as mcal

def get_trading_dates(start: datetime.date, end: datetime.date):
    """Return a list of all NSE trading dates between start and end inclusive."""
    nse = mcal.get_calendar('NSE')
    schedule = nse.schedule(start_date=start, end_date=end)
    return [d.date() for d in schedule.index]

def construct_url(date: datetime.date):
    """Return (url, fmt, filename) for a given trading date.
    Legacy format before 2024-01-01, UDiFF afterwards.
    """
    if date < datetime.date(2024, 1, 1):
        day_str = date.strftime('%d')
        mon_str = date.strftime('%b').upper()
        year_str = date.strftime('%Y')
        filename = f"cm{day_str}{mon_str}{year_str}bhav.csv.zip"
        url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year_str}/CM/{filename}"
        fmt = 'legacy'
    else:
        ymd = date.strftime('%Y%m%d')
        filename = f"BhavCopy_NSE_CM_0_0_0_{ymd}_F_0000.csv.zip"
        url = f"https://nsearchives.nseindia.com/content/cm/{filename}"
        fmt = 'udiff'
    return url, fmt, filename

def download_file(url: str, target: Path, timeout: int = 30):
    """Download a file to target path, returning http_status, size, sha256.
    Raises on failure.
    """
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        http_status = resp.getcode()
        data = resp.read()
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'wb') as f:
            f.write(data)
        size = len(data)
        sha256 = hashlib.sha256(data).hexdigest()
    return http_status, size, sha256

def main():
    parser = argparse.ArgumentParser(description='Download NSE daily bhavcopy archive (2017-2025)')
    parser.add_argument('--start', default='2017-01-01')
    parser.add_argument('--end',   default='2025-12-31')
    args = parser.parse_args()

    start_date = datetime.date.fromisoformat(args.start)
    end_date   = datetime.date.fromisoformat(args.end)
    trading_dates = get_trading_dates(start_date, end_date)

    manifest_path = Path('data/raw/prices/download_manifest.csv')
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open('w', newline='', encoding='utf-8') as mf:
        writer = csv.DictWriter(mf, fieldnames=[
            'date','format','url','download_status','http_status','file_size','sha256','download_timestamp','error'
        ])
        writer.writeheader()
        for d in trading_dates:
            url, fmt, filename = construct_url(d)
            target_dir = Path('data/raw/prices') / fmt
            target_path = target_dir / filename
            # skip if already present
            if target_path.is_file():
                stat = target_path.stat()
                size = stat.st_size
                with open(target_path, 'rb') as f:
                    sha = hashlib.sha256(f.read()).hexdigest()
                writer.writerow({
                    'date': d.isoformat(),
                    'format': fmt,
                    'url': url,
                    'download_status': 'already_present',
                    'http_status': 200,
                    'file_size': size,
                    'sha256': sha,
                    'download_timestamp': datetime.datetime.utcnow().isoformat(),
                    'error': ''
                })
                continue
            # perform download with simple retry logic
            attempts = 3
            for attempt in range(1, attempts+1):
                try:
                    http_status, size, sha = download_file(url, target_path)
                    writer.writerow({
                        'date': d.isoformat(),
                        'format': fmt,
                        'url': url,
                        'download_status': 'downloaded',
                        'http_status': http_status,
                        'file_size': size,
                        'sha256': sha,
                        'download_timestamp': datetime.datetime.utcnow().isoformat(),
                        'error': ''
                    })
                    # Respect rate‑limit of 1 request per second
                    time.sleep(1.0)
                    break
                except urllib.error.HTTPError as e:
                    error_msg = f'HTTPError {e.code}'
                    http_status = e.code
                except urllib.error.URLError as e:
                    error_msg = f'URLError {e.reason}'
                    http_status = ''
                except Exception as e:
                    error_msg = str(e)
                    http_status = ''
                # write failure row for this attempt
                writer.writerow({
                    'date': d.isoformat(),
                    'format': fmt,
                    'url': url,
                    'download_status': f'failed_attempt_{attempt}',
                    'http_status': http_status,
                    'file_size': '',
                    'sha256': '',
                    'download_timestamp': datetime.datetime.utcnow().isoformat(),
                    'error': error_msg
                })
                time.sleep(2 * attempt)  # back‑off
            else:
                # all attempts failed
                writer.writerow({
                    'date': d.isoformat(),
                    'format': fmt,
                    'url': url,
                    'download_status': 'failed',
                    'http_status': http_status,
                    'file_size': '',
                    'sha256': '',
                    'download_timestamp': datetime.datetime.utcnow().isoformat(),
                    'error': error_msg
                })

if __name__ == '__main__':
    main()
