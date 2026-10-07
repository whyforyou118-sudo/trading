"""Development-only momentum information diagnostic.

Scope:
- PIT NIFTY 50 membership
- 12-month formation / 1-month skip
- quarterly signal dates
- development period only: 2018-01-01 through 2022-12-31
- next-quarter raw close-to-close return

Outputs Rank IC and top/bottom decile spread. This is an exploratory
information diagnostic, NOT the Phase 1 performance backtest. It does not
inspect the protected 2023-2025 holdout and cannot authorize changing the
frozen primary strategy.

Important: future returns use raw/unadjusted prices. Therefore corporate-action
and dividend effects are not fully neutralized here. Final inference must use
the Phase 1 corporate-action/dividend ledger.
"""
from __future__ import annotations
import csv, datetime, io, json, math, zipfile
from pathlib import Path
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/phase05_config.json"
CAL=ROOT/"audits/nse_trading_calendar_v3.csv"
MANIFEST=ROOT/"data/raw/prices/download_manifest.csv"
BASELINE=ROOT/"data/reference/nifty50_baseline.csv"
TRANSITIONS=ROOT/"data/reference/nifty50_membership.csv"
EVENTS=ROOT/"data/reference/security_identity_events.csv"
OUT=ROOT/"audits/phase05_development_momentum_diagnostic.csv"
SUMMARY=ROOT/"audits/phase05_development_momentum_summary.csv"

def read(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def parse_file(path):
    def consume(stream):
        reader=csv.DictReader(io.StringIO(stream.read().decode("utf-8-sig")))
        cols=set(reader.fieldnames or [])
        if {"SYMBOL","SERIES","OPEN","CLOSE"}<=cols:
            sk,ser,cl="SYMBOL","SERIES","CLOSE"
        elif {"TckrSymb","SctySrs","OpnPric","ClsPric"}<=cols:
            sk,ser,cl="TckrSymb","SctySrs","ClsPric"
        else:
            raise RuntimeError(f"unknown NSE price schema: {path.name}")
        out={}
        for r in reader:
            if (r.get(ser) or "").strip()!="EQ": continue
            s=(r.get(sk) or "").strip()
            try: out[s]=float(r[cl])
            except (TypeError,ValueError): continue
        return out
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if n.lower().endswith(".csv")]
            if len(names)!=1: raise RuntimeError(f"expected one CSV in {path.name}")
            with z.open(names[0]) as f:return consume(f)
    with path.open("rb") as f:return consume(f)

def spearman(xs,ys):
    n=len(xs)
    if n<3:return float("nan")
    def ranks(v):
        order=sorted(range(n),key=lambda i:v[i])
        r=[0.0]*n; i=0
        while i<n:
            j=i
            while j+1<n and v[order[j+1]]==v[order[i]]: j+=1
            avg=(i+j)/2+1
            for k in range(i,j+1):r[order[k]]=avg
            i=j+1
        return r
    rx,ry=ranks(xs),ranks(ys)
    mx,my=mean(rx),mean(ry)
    num=sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    den=math.sqrt(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))
    return num/den if den else float("nan")

def apply_state(state,transitions,events,through):
    state=dict(state)
    dates=sorted(set([x["effective_date"] for x in transitions]+[x["event_date"] for x in events]))
    for d in dates:
        ed=datetime.date.fromisoformat(d)
        if ed>through: break
        for e in events:
            if e["event_date"]!=d or e.get("apply_to_membership_state","").lower()!="true": continue
            if e["symbol"] in state and state[e["symbol"]]["isin"]==e["old_isin"]:
                state[e["symbol"]]["isin"]=e["new_isin"]
        for r in transitions:
            if r["effective_date"]!=d: continue
            if r["action"]=="INCLUSION":
                state[r["symbol"]]={"company_name":r["company_name"],"isin":r["isin"]}
            elif r["action"]=="EXCLUSION":
                state.pop(r["symbol"],None)
    return state

def main():
    for p in [MANIFEST,BASELINE,TRANSITIONS,CAL]:
        if not p.exists(): raise SystemExit(f"BLOCKED: missing required artifact: {p}")

    dates=sorted(datetime.date.fromisoformat(r["date"]) for r in read(CAL) if r.get("is_trading_day","").lower()=="true")
    md={}
    for d in dates: md[(d.year,d.month)]=d
    manifest={r["date"]:r for r in read(MANIFEST)}
    baseline={r["symbol"]:{"company_name":r["company_name"],"isin":r["isin"]} for r in read(BASELINE)}
    transitions=read(TRANSITIONS)
    events=read(EVENTS) if EVENTS.exists() else []

    # Quarter-end signal dates in development only. Need one quarter ahead
    # for the forward-return diagnostic, hence stop at 2022-09-30.
    signals=[d for d in dates if d.year in range(2018,2023) and d.month in (3,6,9,12)]
    signals=sorted({max(d for d in dates if d.year==s.year and d.month==s.month) for s in signals})
    signals=[s for s in signals if s < datetime.date(2022,10,1)]

    cache={}
    def prices(d):
        key=d.isoformat()
        if key not in cache:
            r=manifest.get(key)
            if not r: raise RuntimeError(f"manifest missing {key}")
            cache[key]=parse_file(ROOT/"data/raw/prices"/r["format"]/Path(r["url"]).name)
        return cache[key]

    out=[]
    for signal in signals:
        # 1M skip: momentum ends at the month before signal month.
        skip_y,skip_m=signal.year,signal.month-1
        if skip_m==0: skip_y,skip_m=skip_y-1,12
        old_y,old_m=skip_y,skip_m-12
        while old_m<=0: old_y,old_m=old_y-1,old_m+12
        end_date=md[(skip_y,skip_m)]
        start_date=md[(old_y,old_m)]

        future=[d for d in dates if d>signal]
        if not future: continue
        next_q=next(d for d in future if d.month in (3,6,9,12) and d>signal)
        p0=prices(start_date); p1=prices(end_date); pf=prices(next_q)
        state=apply_state(baseline,transitions,events,signal)

        candidates=[]
        for symbol in state:
            if symbol not in p0 or symbol not in p1 or symbol not in pf: continue
            a,b,f=p0[symbol],p1[symbol],pf[symbol]
            if min(a,b,f)<=0: continue
            momentum=b/a-1
            forward=f/b-1
            candidates.append((momentum,forward,symbol))

        candidates.sort(reverse=True)
        if len(candidates)<20:
            print(f"SKIP {signal}: only {len(candidates)} complete PIT observations")
            continue

        xs=[x[0] for x in candidates]
        ys=[x[1] for x in candidates]
        ic=spearman(xs,ys)

        n=len(candidates)
        k=max(1,n//10)
        top=mean(x[1] for x in candidates[-k:])
        bottom=mean(x[1] for x in candidates[:k])
        spread=top-bottom

        for rank,(mom,forward,symbol) in enumerate(candidates,1):
            decile=1 if rank<=k else (10 if rank>n-k else None)
            out.append({
                "signal_date":signal.isoformat(),
                "forward_date":next_q.isoformat(),
                "symbol":symbol,
                "cross_section_n":n,
                "momentum_12m_1m_skip":mom,
                "forward_quarter_return_raw":forward,
                "cross_section_rank":rank,
                "decile":decile,
                "rank_ic":ic,
                "top_decile_minus_bottom_decile":spread,
                "data_basis":"RAW_UNADJUSTED_EXPLORATORY",
            })

    if not out: raise SystemExit("BLOCKED: no development diagnostic observations produced")

    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)

    periods=sorted(set(x["signal_date"] for x in out))
    period_stats={}
    for r in out:
        period_stats[r["signal_date"]] = {
            "rank_ic": float(r["rank_ic"]),
            "spread": float(r["top_decile_minus_bottom_decile"]),
        }
    ics=[v["rank_ic"] for _,v in sorted(period_stats.items())]
    spreads=[v["spread"] for _,v in sorted(period_stats.items())]
    summary=[{
        "development_signal_periods":len(periods),
        "development_start":min(periods),
        "development_end":max(periods),
        "mean_rank_ic":mean(ics),
        "median_rank_ic":median(ics),
        "positive_rank_ic_period_fraction":sum(x>0 for x in ics)/len(ics),
        "mean_top_decile_minus_bottom_decile":mean(spreads),
        "median_top_decile_minus_bottom_decile":median(spreads),
        "positive_spread_period_fraction":sum(x>0 for x in spreads)/len(spreads),
        "data_basis":"RAW_UNADJUSTED_EXPLORATORY",
        "holdout_touched":False,
        "strategy_authorization":"NONE",
        "interpretation":"development-only information diagnostic; not final performance inference",
    }]
    with SUMMARY.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=summary[0].keys()); w.writeheader(); w.writerows(summary)

    print("PHASE 0.5 DEVELOPMENT-ONLY MOMENTUM DIAGNOSTIC")
    print(f"Signal periods: {len(periods)}")
    print(f"Development: {periods[0]} -> {periods[-1]}")
    print(f"Mean Rank IC: {summary[0]['mean_rank_ic']:.6f}")
    print(f"Median Rank IC: {summary[0]['median_rank_ic']:.6f}")
    print(f"Positive Rank IC periods: {summary[0]['positive_rank_ic_period_fraction']:.2%}")
    print(f"Mean top-decile minus bottom-decile spread: {summary[0]['mean_top_decile_minus_bottom_decile']:.6%}")
    print(f"Median spread: {summary[0]['median_top_decile_minus_bottom_decile']:.6%}")
    print(f"Positive spread periods: {summary[0]['positive_spread_period_fraction']:.2%}")
    print("Holdout touched: FALSE")
    print("Strategy authorization: NONE")
    print(f"Wrote: {OUT}")
    print(f"Wrote: {SUMMARY}")
    print("WARNING: raw-price exploratory diagnostic; final Phase 1 inference must use the corporate-action/dividend ledger.")

if __name__=="__main__": raise SystemExit(main())
