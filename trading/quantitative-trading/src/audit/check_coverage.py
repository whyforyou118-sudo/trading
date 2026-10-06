"""Deterministic audit of raw NSE bhavcopy files."""
from __future__ import annotations
import csv,datetime,io,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/"data"/"raw"/"prices"; OUT=ROOT/"audits"
def infer_date(filename):
    n=Path(filename).name
    try:
        if n.startswith("cm") and "bhav.csv" in n:return datetime.datetime.strptime(n[2:11],"%d%b%Y").date().isoformat()
        if n.startswith("BhavCopy_NSE_CM_0_0_0_"):return datetime.datetime.strptime(n.split("_")[6],"%Y%m%d").date().isoformat()
    except (ValueError,IndexError):pass
    return ""

def parse_stream(stream,name):
    r={"filename":name,"trading_date":infer_date(name),"row_count":0,"unique_symbols":set(),"duplicate_rows":0,"missing_ohlc":0,"invalid_ohlc":0,"nonpositive_price":0,"volume_anomalies":0,"missing_isin":0,"schema_consistency":"","error":""}
    try:
        reader=csv.DictReader(io.StringIO(stream.read().decode("utf-8-sig"))); cols=set(reader.fieldnames or [])
        if {"SYMBOL","SERIES","OPEN","HIGH","LOW","CLOSE","TOTTRDQTY","ISIN"}<=cols: keys=("SYMBOL","SERIES","OPEN","HIGH","LOW","CLOSE","TOTTRDQTY","ISIN"); r["schema_consistency"]="legacy"
        elif {"TckrSymb","SctySrs","OpnPric","HghPric","LwPric","ClsPric","TtlTradgVol","ISIN"}<=cols: keys=("TckrSymb","SctySrs","OpnPric","HghPric","LwPric","ClsPric","TtlTradgVol","ISIN"); r["schema_consistency"]="udiff"
        else:r["error"]="unknown schema";return r
        sk,ser,ok,hk,lk,ck,vk,ik=keys; seen=set()
        for row in reader:
            r["row_count"]+=1; sym=(row.get(sk) or "").strip(); series=(row.get(ser) or "").strip()
            if series=="EQ":r["unique_symbols"].add(sym)
            key=(sym,series)
            if key in seen:r["duplicate_rows"]+=1
            seen.add(key)
            try:o,h,l,c=[float(row.get(k) or 0) for k in (ok,hk,lk,ck)]
            except (TypeError,ValueError):r["missing_ohlc"]+=1;continue
            if not(l<=o<=h and l<=c<=h):r["invalid_ohlc"]+=1
            if min(o,h,l,c)<=0:r["nonpositive_price"]+=1
            try:
                if float(row.get(vk) or 0)<0:r["volume_anomalies"]+=1
            except (TypeError,ValueError):r["volume_anomalies"]+=1
            if not(row.get(ik) or "").strip():r["missing_isin"]+=1
    except Exception as e:r["error"]=str(e)
    return r

def parse_file(path):
    if path.suffix.lower()==".zip":
        try:
            with zipfile.ZipFile(path) as z:
                names=[n for n in z.namelist() if n.lower().endswith(".csv")]
                if len(names)!=1:return {"filename":str(path),"trading_date":infer_date(path.name),"row_count":0,"unique_symbols":set(),"duplicate_rows":0,"missing_ohlc":0,"invalid_ohlc":0,"nonpositive_price":0,"volume_anomalies":0,"missing_isin":0,"schema_consistency":"","error":"ZIP must contain exactly one CSV"}
                with z.open(names[0]) as f:return parse_stream(f,str(path))
        except zipfile.BadZipFile as e:return {"filename":str(path),"trading_date":infer_date(path.name),"row_count":0,"unique_symbols":set(),"duplicate_rows":0,"missing_ohlc":0,"invalid_ohlc":0,"nonpositive_price":0,"volume_anomalies":0,"missing_isin":0,"schema_consistency":"","error":f"invalid ZIP: {e}"}
    with path.open("rb") as f:return parse_stream(f,str(path))

def main():
    paths=sorted(list(RAW.rglob("*.zip"))+list(RAW.rglob("*.csv")))
    paths=[p for p in paths if "sample" not in p.parts]
    if not paths:
        print("PRICE COVERAGE: BLOCKED — no full raw archive files found");return 2
    rows=[parse_file(p) for p in paths]; OUT.mkdir(parents=True,exist_ok=True)
    fields=["filename","trading_date","row_count","unique_symbols","duplicate_rows","missing_ohlc","invalid_ohlc","nonpositive_price","volume_anomalies","missing_isin","schema_consistency","error"]
    with (OUT/"full_price_coverage.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:
            x=dict(r);x["unique_symbols"]=";".join(sorted(r["unique_symbols"]));w.writerow(x)
    bad=[r for r in rows if r["error"] or any(r[k] for k in ["duplicate_rows","missing_ohlc","invalid_ohlc","nonpositive_price","volume_anomalies","missing_isin"])]
    dates=[r["trading_date"] for r in rows if r["trading_date"]]
    with (OUT/"full_price_coverage.md").open("w",encoding="utf-8") as f:
        f.write(f"# Full Price Coverage Audit\n\nFiles: {len(rows)}\nRows: {sum(r['row_count'] for r in rows):,}\nDates: {min(dates) if dates else ''} – {max(dates) if dates else ''}\nBad files: {len(bad)}\n")
    print(f"PRICE COVERAGE: {'PASS' if not bad else 'FAIL'} — {len(rows)} files, {sum(r['row_count'] for r in rows):,} rows, {len(bad)} bad files")
    return 1 if bad else 0
if __name__=="__main__":raise SystemExit(main())
