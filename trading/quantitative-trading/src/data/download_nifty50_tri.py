"""Download daily NIFTY 50 Total Return Index (TRI) from Nifty Indices.
Uses the official historical-data endpoint in <=365-day chunks.
The output is a reference dataset, not a performance result.
"""
from __future__ import annotations
import argparse,csv,datetime,json,os,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/reference/nifty50_tri.csv"
URL="https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString"
FIELDS=["date","value","source","source_reference"]

TRI_URL="https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString"
TRI_REFERER="https://www.niftyindices.com/reports/historical-data"
TRI_UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")

def make_session():
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError(
            "httpx is required for NIFTY 50 TRI access. Install with: python -m pip install httpx"
        ) from exc
    return httpx.Client(
        headers={
            "Content-Type":"application/json; charset=UTF-8",
            "X-Requested-With":"XMLHttpRequest",
            "Referer":TRI_REFERER,
            "User-Agent":TRI_UA,
        },
        follow_redirects=True,
        timeout=120.0,
    )

def request_chunk(session,start,end):
    # The ASP.NET endpoint expects cinfo as a JSON-like string with
    # single-quoted fields, not a nested JSON object.
    cinfo=("{'name':'NIFTY 50',"
           f"'startDate':'{start:%d-%b-%Y}',"
           f"'endDate':'{end:%d-%b-%Y}',"
           "'indexName':'NIFTY 50'}")
    payload={"cinfo":cinfo}
    data=json.dumps(payload).encode()
    r=session.post(TRI_URL,content=json.dumps(payload))
    if r.status_code != 200:
        raise RuntimeError(f"Nifty Indices TRI HTTP {r.status_code}: {r.text[:500]!r}")
    if r.headers.get("content-type","").lower().split(";")[0] != "application/json":
        raise RuntimeError(
            f"Nifty Indices TRI returned {r.headers.get('content-type')!r}; "
            f"location={r.headers.get('location')!r}; body={r.text[:500]!r}"
        )
    raw=r.text.lstrip("\ufeff").strip()
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
    session=make_session()
    all_rows={}
    cur=start
    while cur<=end:
        chunk_end=min(cur+datetime.timedelta(days=364),end)
        print(f"Downloading TRI: {cur} -> {chunk_end}")
        for row in request_chunk(session,cur,chunk_end): all_rows[row["date"]]=row
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
