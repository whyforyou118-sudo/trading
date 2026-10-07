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

TRI_URL="https://www.niftyindices.com/Backpage/getTotalReturnIndexString"
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
    parameters={
        "name":"NIFTY 50",
        "startDate":start.strftime("%d-%b-%Y"),
        "endDate":end.strftime("%d-%b-%Y"),
        "indexName":"NIFTY 50",
    }
    payload={"cinfo":json.dumps(parameters)}
    r=session.post(TRI_URL,content=json.dumps(payload))
    if r.status_code != 200:
        raise RuntimeError(f"Nifty Indices TRI HTTP {r.status_code}: {r.text[:500]!r}")
    raw=r.text.lstrip("\ufeff").strip()
    # Nifty currently labels this endpoint text/html even when the body is
    # valid JSON. Validate the payload itself rather than trusting MIME type.
    if not raw or raw[:1] not in "{[":
        raise RuntimeError(
            f"Nifty Indices TRI returned non-JSON content: "
            f"content_type={r.headers.get('content-type')!r}; body={raw[:500]!r}"
        )
    try:
        obj=json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Nifty Indices TRI returned invalid JSON: {raw[:500]!r}"
        ) from exc
    # Nifty has returned both a wrapper object and a bare JSON list.
    # Normalize the root before iterating records.
    if isinstance(obj, dict):
        raw=obj.get("d",obj)
    elif isinstance(obj, list):
        raw=obj
    else:
        raise RuntimeError(
            f"Unexpected TRI JSON root: {type(obj).__name__}: {str(obj)[:500]!r}"
        )

    if isinstance(raw,str):
        try:
            raw=json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Nifty TRI field 'd' is not valid JSON: {raw[:500]!r}"
            ) from exc

    if not isinstance(raw,list):
        raise RuntimeError(
            f"Unexpected TRI record payload: {type(raw).__name__}: {str(raw)[:500]!r}"
        )
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
