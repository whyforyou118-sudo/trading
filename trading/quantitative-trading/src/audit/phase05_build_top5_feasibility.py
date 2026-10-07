"""Build the Phase 0.5 Top-5 affordability input.

This computes only the frozen signal ranking and next-session opening prices needed
to test whole-share affordability. It produces no portfolio P&L.

IMPORTANT:
- Price basis is RAW_UNADJUSTED.
- This is a feasibility diagnostic before the Phase 1A corporate-action ledger.
- It must not be used as the strategy performance dataset.
"""
from __future__ import annotations
import csv,datetime,io,json,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"
CAL=ROOT/"audits/nse_trading_calendar_v3.csv"
MANIFEST=ROOT/"data/raw/prices/download_manifest.csv"
BASELINE=ROOT/"data/reference/nifty50_baseline.csv"
TRANSITIONS=ROOT/"data/reference/nifty50_membership.csv"
EVENTS=ROOT/"data/reference/security_identity_events.csv"
OUT=ROOT/"audits/phase05_top5_feasibility.csv"

def read(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def parse_file(path):
    def consume(stream):
        reader=csv.DictReader(io.StringIO(stream.read().decode("utf-8-sig")))
        cols=set(reader.fieldnames or [])
        if {"SYMBOL","SERIES","OPEN","CLOSE"}<=cols:
            sk,ser,op,cl="SYMBOL","SERIES","OPEN","CLOSE"
        elif {"TckrSymb","SctySrs","OpnPric","ClsPric"}<=cols:
            sk,ser,op,cl="TckrSymb","SctySrs","OpnPric","ClsPric"
        else: raise RuntimeError(f"unknown NSE price schema: {path.name}")
        out={}
        for r in reader:
            if (r.get(ser) or "").strip()!="EQ": continue
            s=(r.get(sk) or "").strip()
            try: out[s]={"open":float(r[op]),"close":float(r[cl])}
            except (TypeError,ValueError): continue
        return out
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if n.lower().endswith(".csv")]
            if len(names)!=1: raise RuntimeError(f"expected one CSV in {path.name}")
            with z.open(names[0]) as f:return consume(f)
    with path.open("rb") as f:return consume(f)

def build_calendar():
    rows=read(CAL)
    return sorted(datetime.date.fromisoformat(r["date"]) for r in rows if r.get("is_trading_day","").lower()=="true")

def month_end_map(dates):
    out={}
    for d in dates: out[(d.year,d.month)]=d
    return out

def apply_state(state, transitions, events, through):
    state=dict(state)
    for d in sorted(set([x["effective_date"] for x in transitions]+[x["event_date"] for x in events])):
        ed=datetime.date.fromisoformat(d)
        if ed>through: break
        for e in events:
            if e["event_date"]!=d or e.get("apply_to_membership_state","").lower()!="true": continue
            if e["symbol"] in state and state[e["symbol"]]["isin"]==e["old_isin"]:
                state[e["symbol"]]["isin"]=e["new_isin"]
        for r in transitions:
            if r["effective_date"]!=d: continue
            if r["action"]=="INCLUSION": state[r["symbol"]]={"company_name":r["company_name"],"isin":r["isin"]}
            elif r["action"]=="EXCLUSION": state.pop(r["symbol"],None)
    return state

def main():
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    for p in [MANIFEST,BASELINE,TRANSITIONS,CAL]:
        if not p.exists(): raise SystemExit(f"BLOCKED: missing required Phase 0 artifact: {p}")
    dates=build_calendar(); md=month_end_map(dates)
    manifest={r["date"]:r for r in read(MANIFEST)}
    baseline={r["symbol"]:{"company_name":r["company_name"],"isin":r["isin"]} for r in read(BASELINE)}
    transitions=read(TRANSITIONS); events=read(EVENTS) if EVENTS.exists() else []
    quarters=[d for d in dates if d.year>=2018 and d.year<=2025 and d.month in (3,6,9,12)]
    qend={}
    for d in quarters:qend[(d.year,d.month)]=max(d,qend.get((d.year,d.month),d))
    signals=sorted(qend.values())

    cache={}
    def prices(d):
        key=d.isoformat()
        if key in cache:return cache[key]
        r=manifest.get(key)
        if not r: raise RuntimeError(f"manifest missing {key}")
        path=ROOT/"data/raw/prices"/r["format"]/Path(r["url"]).name
        cache[key]=parse_file(path); return cache[key]

    out=[]
    for signal in signals:
        prev_month=(signal.year,signal.month-1) if signal.month>1 else (signal.year-1,12)
        old_year=signal.year; old_month=signal.month-13
        while old_month<=0: old_month+=12; old_year-=1
        end_price_date=md[prev_month]; start_price_date=md[(old_year,old_month)]
        next_dates=[d for d in dates if d>signal]
        if not next_dates: continue
        exec_date=next_dates[0]
        p_end=prices(end_price_date); p_start=prices(start_price_date); p_exec=prices(exec_date)
        state=apply_state(baseline,transitions,events,signal)
        scores=[]
        for symbol in state:
            if symbol not in p_end or symbol not in p_start: continue
            a=p_end[symbol]["close"]; b=p_start[symbol]["close"]
            if a<=0 or b<=0: continue
            scores.append((a/b-1.0,symbol))
        scores.sort(reverse=True)
        for rank,(score,symbol) in enumerate(scores[:int(cfg["primary_holdings"])],1):
            if symbol not in p_exec: continue
            out.append({
                "rebalance_date":signal.isoformat(),"execution_date":exec_date.isoformat(),
                "rank":rank,"symbol":symbol,"momentum_raw_unadjusted":score,
                "execution_price":p_exec[symbol]["open"],"price_basis":"RAW_UNADJUSTED"
            })
    if not out: raise SystemExit("BLOCKED: no Top-5 feasibility rows produced")
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
    print("PHASE 0.5 TOP-5 FEASIBILITY INPUT")
    print(f"Rebalance dates: {len(set(r['rebalance_date'] for r in out))}")
    print(f"Rows: {len(out)}")
    print(f"Artifact: {OUT}")
    print("WARNING: raw-unadjusted ranking is for affordability feasibility only; do not use it for performance results.")
    return 0

if __name__=="__main__": raise SystemExit(main())
