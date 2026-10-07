"""Download daily NIFTY 50 Total Return Index (TRI) from Nifty Indices.
Uses the official historical-data endpoint in <=365-day chunks.
The output is a reference dataset, not a performance result.
"""
from __future__ import annotations
import argparse,csv,datetime,json,os,tempfile,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/reference/nifty50_tri.csv"
URL="https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString"
FIELDS=["date","value","source","source_reference"]

def request_chunk(start,end):
    payload={"cinfo":json.dumps({
        "name":"NIFTY 50","startDate":start.strftime("%d %b %Y"),
        "endDate":end.strftime("%d %b %Y"),"indexName":"NIFTY 50"
    })}
    data=json.dumps(payload).encode()
    req=urllib.request.Request(URL,data=data,headers={
        "Content-Type":"application/json; charset=UTF-8",
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154.0 Safari/537.36",
        "Referer":"https://www.niftyindices.com/reports/historical-data"
    },method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:
        obj=json.loads(r.read().decode("utf-8"))
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
