import csv, datetime, hashlib, os, urllib.request, urllib.error, json
from pathlib import Path

# Sample trading dates (known weekdays, likely trading days)
sample_dates = [
    datetime.date(2017, 2, 1),   # Thu
    datetime.date(2018, 5, 2),   # Wed
    datetime.date(2019, 9, 30),  # Mon
    datetime.date(2020, 12, 31), # Thu (last trading day of 2020)
    datetime.date(2021, 7, 15),  # Thu
    datetime.date(2022, 3, 25),  # Fri
    datetime.date(2023, 11, 1),  # Wed
    datetime.date(2024, 6, 20),  # Thu (UDiFF format)
    datetime.date(2025, 8, 15),  # Fri (UDiFF format)
]

def construct_url(date: datetime.date):
    if date < datetime.date(2024, 1, 1):
        day = date.strftime('%d')
        mon = date.strftime('%b').upper()
        year = date.strftime('%Y')
        filename = f"cm{day}{mon}{year}bhav.csv.zip"
        url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year}/CM/{filename}"
        fmt = 'legacy'
    else:
        ymd = date.strftime('%Y%m%d')
        filename = f"BhavCopy_NSE_CM_0_0_0_{ymd}_F_0000.csv.zip"
        url = f"https://nsearchives.nseindia.com/content/cm/{filename}"
        fmt = 'udiff'
    return url, fmt

def head_request(url: str):
    req = urllib.request.Request(url, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.getcode()
            size = resp.headers.get('Content-Length')
            size = int(size) if size else None
            return status, size
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return None, None

out_path = Path('audits/real_date_download_test.csv')
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['date','url','http_status','file_exists','download_success','file_size','format','sha256'])
    writer.writeheader()
    for d in sample_dates:
        url, fmt = construct_url(d)
        status, size = head_request(url)
        file_exists = (status == 200)
        download_success = False
        sha = ''
        if file_exists:
            # download first 1KB to compute a quick hash
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    data = resp.read(1024)
                    sha = hashlib.sha256(data).hexdigest()
                    download_success = True
            except Exception:
                download_success = False
        writer.writerow({
            'date': d.isoformat(),
            'url': url,
            'http_status': status if status is not None else '',
            'file_exists': file_exists,
            'download_success': download_success,
            'file_size': size if size is not None else '',
            'format': fmt,
            'sha256': sha,
        })
print('Test CSV written to', out_path)
