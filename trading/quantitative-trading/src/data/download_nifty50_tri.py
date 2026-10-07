"""Download daily NIFTY 50 Total Return Index (TRI) from Nifty Indices.
Uses the official historical-data endpoint in <=365-day chunks.
The output is a reference dataset, not a performance result.
"""
from __future__ import annotations
import argparse,csv,datetime,json,os,tempfile,urllib.request,http.cookiejar
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/reference/nifty50_tri.csv"
URL="https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString"
FIELDS=["date","value","source","source_reference"]

_UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36")
BASE="https://www.niftyindices.com"
TRI_URL=BASE+"/Backpage.aspx/getTotalReturnIndexString"
REFERER=BASE+"/reports/historical-data"
COOKIE_JAR=http.cookiejar.CookieJar()
OPENER=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIE_JAR))

def warm_session():
    req=urllib.request.Request(REFERER,headers={"User-Agent":_UA,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    with OPENER.open(req,timeout=60) as r: r.read(1024)
    if not COOKIE_JAR: raise RuntimeError("Nifty Indices historical-data page returned no session cookies")

def request_chunk(start,end):
    # The ASP.NET endpoint expects cinfo as a JSON-like string with
    # single-quoted fields, not a nested JSON object.
    cinfo=("{'name':'NIFTY 50',"
           f"'startDate':'{start:%d-%b-%Y}',"
           f"'endDate':'{end:%d-%b-%Y}',"
           "'indexName':'NIFTY 50'}")
    payload={"cinfo":cinfo}
    data=json.dumps(payload).encode()
    req=urllib.request.Request(TRI_URL,data=data,headers={
        "Content-Type":"application/json; charset=UTF-8",
        "X-Requested-With":"XMLHttpRequest",
        "Accept":"application/json, text/javascript, */*; q=0.01",
        "User-Agent":_UA,
        "Referer":REFERER,
        "Origin":BASE
    },method="POST")
    with OPENER.open(req,timeout=120) as r:
        raw=r.read().decode("utf-8-sig").strip()
        if not raw or raw[:1] not in "{[":
            raise RuntimeError(f"Nifty Indices returned non-JSON response: {raw[:200]!r}")
        obj=json.loads(raw)
    raw=obj.get("d",obj)
    if isinstance(raw,str): raw=json.loads(raw)
    if not isinstance(raw,list): raise RuntimeError(f"Unexpected TRI response: {type(raw)}")
    rows=[]
    for x in raw:
        ds=x.get("Date") or x.get("HistoricalDate")
        val=x.get("TotalReturnsIndex")
        if not ds or val in (None,""): continue
        d=datetime.datetime.strptime(ds,"%d %b %Y").date()
        rows.append({"date":d.isoformat(),"value":float(val),
                     "source":"Nifty Indices Historical Data — Total Returns Index Values",
                     "source_reference":"https://www.niftyindices.com/reports/historical-data"})
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--start",default="2018-01-01")
    ap.add_argument("--end",default="2025-12-31")
    args=ap.parse_args()
    start,end=datetime.date.fromisoformat(args.start),datetime.date.fromisoformat(args.end)
    if end<start: raise SystemExit("end must be >= start")
    all_rows={}
    cur=start
    while cur<=end:
        chunk_end=min(cur+datetime.timedelta(days=364),end)
        print(f"Downloading TRI: {cur} -> {chunk_end}")
        for row in request_chunk(cur,chunk_end): all_rows[row["date"]]=row
        cur=chunk_end+datetime.timedelta(days=1)
    rows=[all_rows[k] for k in sorted(all_rows)]
    if not rows: raise SystemExit("No TRI observations returned")
    if len(rows)!=len(set(r["date"] for r in rows)): raise SystemExit("Duplicate TRI dates")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix="nifty50_tri.",suffix=".csv",dir=str(OUT.parent)); os.close(fd)
    try:
        with open(tmp,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
        os.replace(tmp,OUT)
    finally:
        try: os.unlink(tmp)
        except OSError: pass
    print(f"Wrote {len(rows)} TRI observations: {OUT}")
    print(f"Coverage: {rows[0]['date']} -> {rows[-1]['date']}")
    return 0

if __name__=="__main__": raise SystemExit(main())
