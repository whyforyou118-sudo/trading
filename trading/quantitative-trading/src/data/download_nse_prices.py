"""Download the immutable NSE daily CM bhavcopy archive.

The verified project calendar is the sole source of requested trading dates.
pandas_market_calendars is deliberately not used for research-date selection.
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,os,tempfile,time,urllib.error,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CALENDAR=ROOT/"audits"/"nse_trading_calendar_v3.csv"
RAW=ROOT/"data"/"raw"/"prices"
MANIFEST=RAW/"download_manifest.csv"
FIELDS=["date","format","url","download_status","http_status","file_size","sha256","download_timestamp","error"]

def get_trading_dates(start,end):
    if not CALENDAR.exists(): raise RuntimeError(f"verified calendar missing: {CALENDAR}")
    out=[]
    with CALENDAR.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            d=datetime.date.fromisoformat(r["date"])
            if start<=d<=end and r.get("is_trading_day","").strip().lower()=="true":
                if r.get("validation_status","").upper()!="VALIDATED":
                    raise RuntimeError(f"calendar row is not validated: {d}")
                out.append(d)
    if len(out)!=len(set(out)): raise RuntimeError("calendar contains duplicate trading dates")
    return out

def construct_url(date):
    if date<datetime.date(2024,1,1):
        filename=f"cm{date:%d}{date:%b}".upper()+f"{date:%Y}bhav.csv.zip"
        return f"https://archives.nseindia.com/content/historical/EQUITIES/{date:%Y}/{date:%b}".upper()+f"/{filename}","legacy",filename
    filename=f"BhavCopy_NSE_CM_0_0_0_{date:%Y%m%d}_F_0000.csv.zip"
    return f"https://nsearchives.nseindia.com/content/cm/{filename}","udiff",filename

def sha256_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def download(url,target,timeout=60):
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=target.name+".",dir=str(target.parent))
    os.close(fd)
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154.0 Safari/537.36","Referer":"https://www.nseindia.com/all-reports"})
        with urllib.request.urlopen(req,timeout=timeout) as resp:
            status=resp.getcode()
            with open(tmp,"wb") as f:
                while True:
                    chunk=resp.read(1024*1024)
                    if not chunk: break
                    f.write(chunk)
        os.replace(tmp,target)
        return status,target.stat().st_size,sha256_file(target)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

def load_manifest():
    rows={}
    if MANIFEST.exists():
        with MANIFEST.open("r",encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f):
                d=r.get("date","")
                if d: rows[d]=r
    return rows

def save_manifest(rows):
    MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="download_manifest.",suffix=".csv",dir=str(MANIFEST.parent))
    os.close(fd)
    try:
        with open(tmp,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader()
            for d in sorted(rows): w.writerow(rows[d])
        os.replace(tmp,MANIFEST)
    finally:
        try: os.unlink(tmp)
        except OSError: pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--start",default="2017-01-01"); ap.add_argument("--end",default="2025-12-31")
    ap.add_argument("--sleep",type=float,default=1.0)
    args=ap.parse_args()
    start,end=datetime.date.fromisoformat(args.start),datetime.date.fromisoformat(args.end)
    dates=get_trading_dates(start,end)
    manifest=load_manifest()
    print(f"Verified trading dates requested: {len(dates)}")
    failures=0
    for i,d in enumerate(dates,1):
        url,fmt,filename=construct_url(d); target=RAW/fmt/filename
        key=d.isoformat()
        existing=manifest.get(key)
        if existing and existing.get("download_status") in {"downloaded","already_present"} and target.exists():
            digest=sha256_file(target)
            if digest==existing.get("sha256") and existing.get("http_status")=="200":
                continue
        last_error=""; status=""
        for attempt in range(1,4):
            try:
                status,size,digest=download(url,target)
                manifest[key]={"date":key,"format":fmt,"url":url,"download_status":"downloaded",
                    "http_status":str(status),"file_size":str(size),"sha256":digest,
                    "download_timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"error":""}
                save_manifest(manifest); time.sleep(args.sleep); break
            except urllib.error.HTTPError as e:
                status=str(e.code); last_error=f"HTTPError {e.code}"
            except urllib.error.URLError as e:
                status=""; last_error=f"URLError {e.reason}"
            except Exception as e:
                status=""; last_error=str(e)
            time.sleep(2*attempt)
        else:
            failures+=1
            manifest[key]={"date":key,"format":fmt,"url":url,"download_status":"failed",
                "http_status":status,"file_size":"","sha256":"",
                "download_timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"error":last_error}
            save_manifest(manifest)
        if i%25==0 or failures:
            print(f"{i}/{len(dates)} processed; failures={failures}")
    print(f"Completed with terminal failures: {failures}")
    return 1 if failures else 0

if __name__=="__main__": raise SystemExit(main())
