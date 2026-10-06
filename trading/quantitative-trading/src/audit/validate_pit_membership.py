"""Point-in-time NIFTY 50 membership reconstruction audit."""
from __future__ import annotations
import csv,datetime,zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; REFERENCE=ROOT/"data"/"reference"; RAW=ROOT/"data"/"raw"/"prices"
TRANSITIONS=REFERENCE/"nifty50_membership.csv"; BASELINE=REFERENCE/"nifty50_baseline.csv"; EVENTS=REFERENCE/"security_identity_events.csv"; OUT=ROOT/"audits"/"pit_membership_reconstruction.csv"
BASELINE_DATE=datetime.date(2017,3,31)

@dataclass(frozen=True)
class Security: symbol:str; company_name:str; isin:str

def read_csv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def file_date(path):
    n=path.name
    try:
        if n.startswith("cm") and "bhav.csv" in n:return datetime.datetime.strptime(n[2:11],"%d%b%Y").date()
        if n.startswith("BhavCopy_NSE_CM_0_0_0_"):return datetime.datetime.strptime(n.split("_")[6],"%Y%m%d").date()
    except (ValueError,IndexError):pass
    return None

def load_baseline():
    rows=read_csv(BASELINE)
    if len(rows)!=51: raise RuntimeError(f"2017-03-31 baseline expected 51 rows; found {len(rows)}")
    out={}
    for r in rows:
        s=r["symbol"].strip(); isin=r.get("isin","").strip()
        if not s or s in out: raise RuntimeError(f"invalid/duplicate baseline symbol: {s}")
        if not isin: raise RuntimeError(f"baseline ISIN missing for {s}")
        out[s]=Security(s,r["company_name"].strip(),isin)
    return out
def load_transitions():
    rows=read_csv(TRANSITIONS); required={"effective_date","symbol","company_name","isin","action"}
    if not rows or not required<=set(rows[0]):raise RuntimeError("membership ledger missing/invalid schema")
    for r in rows:
        datetime.date.fromisoformat(r["effective_date"])
        if r["action"] not in {"INCLUSION","EXCLUSION"}:raise RuntimeError(f"unknown action: {r['action']}")
    return sorted(rows,key=lambda r:(r["effective_date"],r["symbol"],r["action"]))

def main():
    try:
        members=load_baseline(); transitions=load_transitions(); events=read_csv(EVENTS) if EVENTS.exists() else []
        results=[]
        all_dates=sorted({r["effective_date"] for r in transitions}|{r["event_date"] for r in events if r.get("apply_to_membership_state","").lower()=="true"})
        for date in all_dates:
            proposed=dict(members); errors=[]
            for e in [x for x in events if x.get("event_date")==date and x.get("apply_to_membership_state","").lower()=="true"]:
                if e["symbol"] in proposed:
                    cur=proposed[e["symbol"]]
                    if cur.isin!=e["old_isin"]: errors.append(f"identity event old ISIN mismatch for {e['symbol']}: ledger={e['old_isin']}, current={cur.isin}")
                    else: proposed[e["symbol"]]=Security(cur.symbol,cur.company_name,e["new_isin"])
                else: errors.append(f"identity event symbol absent: {e['symbol']}")
            for r in [x for x in transitions if x["effective_date"]==date]:
                s,i,a=r["symbol"],r["isin"],r["action"]
                if a=="INCLUSION":
                    if s in proposed:errors.append(f"inclusion already present: {s}")
                    if any(v.isin==i for v in proposed.values()):errors.append(f"inclusion ISIN already present: {i}")
                    proposed[s]=Security(s,r["company_name"],i)
                else:
                    if s not in proposed:errors.append(f"exclusion absent: {s}")
                    else:
                        if proposed[s].isin!=i:errors.append(f"exclusion ISIN mismatch for {s}: ledger={i}, current={proposed[s].isin}")
                        del proposed[s]
            dup=[i for i,n in Counter(v.isin for v in proposed.values()).items() if n>1]
            if dup:errors.append("duplicate ISINs: "+",".join(dup))
            expected=51 if date<"2017-09-29" else 50
            if len(proposed)!=expected:errors.append(f"membership count={len(proposed)}, expected {expected}")
            results.append({"effective_date":date,"transition_rows":sum(x["effective_date"]==date for x in transitions),"member_count":len(proposed),"duplicate_isins":";".join(dup),"status":"PASS" if not errors else "FAIL","errors":" | ".join(errors)})
            if errors:break
            members=proposed
        OUT.parent.mkdir(parents=True,exist_ok=True)
        with OUT.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["effective_date","transition_rows","member_count","duplicate_isins","status","errors"]);w.writeheader();w.writerows(results)
        if any(r["status"]=="FAIL" for r in results):print("PIT MEMBERSHIP: FAIL\n"+next(r["errors"] for r in results if r["status"]=="FAIL"));return 1
        print(f"Effective states checked: {len(results)}\nPIT MEMBERSHIP: PASS");return 0
    except RuntimeError as e:print(f"PIT MEMBERSHIP: BLOCKED — {e}");return 2

if __name__=="__main__":raise SystemExit(main())
