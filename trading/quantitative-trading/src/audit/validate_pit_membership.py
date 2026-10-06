"""Point-in-time NIFTY 50 membership reconstruction audit.

Security identity is time-varying: a ticker may legitimately map to more than one
ISIN across a corporate reconstruction/transition. The ledger is authoritative for
membership events; raw exchange files are used only to corroborate identity.
"""
from __future__ import annotations
import csv, datetime, zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REFERENCE=ROOT/"data"/"reference"; RAW=ROOT/"data"/"raw"/"prices"
TRANSITIONS=REFERENCE/"nifty50_membership.csv"; BASELINE=REFERENCE/"nifty50_baseline.csv"
OUT=ROOT/"audits"/"pit_membership_reconstruction.csv"

@dataclass(frozen=True)
class Security:
    symbol:str; company_name:str; isin:str

def read_csv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def raw_symbol_isins(symbols):
    found=defaultdict(set)
    for path in sorted(list(RAW.rglob("*.csv"))+list(RAW.rglob("*.zip"))):
        try:
            if path.suffix.lower()==".zip":
                with zipfile.ZipFile(path) as zf:
                    names=[n for n in zf.namelist() if n.lower().endswith(".csv")]
                    streams=[zf.open(n,"r") for n in names]
            else: streams=[path.open("rb")]
            for stream in streams:
                try:
                    rows=csv.DictReader(stream.read().decode("utf-8-sig").splitlines())
                    cols=set(rows.fieldnames or [])
                    if not ({"SYMBOL","SERIES","ISIN"}<=cols or {"TckrSymb","SctySrs","ISIN"}<=cols): continue
                    sk,ser="SYMBOL","SERIES" if "SYMBOL" in cols else "TckrSymb","SctySrs"
                    for row in rows:
                        sym=(row.get(sk) or "").strip(); series=(row.get(ser) or "").strip()
                        isin=(row.get("ISIN") or "").strip()
                        if sym in symbols and series=="EQ" and isin: found[sym].add(isin)
                finally: stream.close()
        except (zipfile.BadZipFile,UnicodeDecodeError): continue
    return found

def load_baseline():
    rows=read_csv(BASELINE)
    if len(rows)!=51: raise RuntimeError(f"2017-03-31 baseline expected 51 rows; found {len(rows)}")
    out={}
    for r in rows:
        s=r["symbol"].strip()
        if not s or s in out: raise RuntimeError(f"invalid/duplicate baseline symbol: {s}")
        out[s]=Security(s,r["company_name"].strip(),r.get("isin","").strip())
    return out

def load_transitions():
    rows=read_csv(TRANSITIONS)
    required={"effective_date","symbol","company_name","isin","action"}
    if not rows or not required<=set(rows[0]): raise RuntimeError("membership ledger missing/invalid schema")
    for r in rows:
        datetime.date.fromisoformat(r["effective_date"])
        if r["action"] not in {"INCLUSION","EXCLUSION"}: raise RuntimeError(f"unknown action: {r['action']}")
    return sorted(rows,key=lambda r:(r["effective_date"],r["symbol"],r["action"]))

def main():
    try:
        members=load_baseline()
        transitions=load_transitions()
        # Baseline identity must be complete before reconstruction.
        unresolved=[s for s,v in members.items() if not v.isin]
        if unresolved:
            raw=raw_symbol_isins(set(unresolved))
            members={s:Security(v.symbol,v.company_name,raw.get(s,{""}).pop() if len(raw.get(s,set()))==1 else v.isin)
                     for s,v in members.items()}
        unresolved=[s for s,v in members.items() if not v.isin]
        if unresolved: raise RuntimeError("baseline ISINs unresolved: "+", ".join(sorted(unresolved)))

        results=[]
        for date in sorted({r["effective_date"] for r in transitions}):
            proposed=dict(members); errors=[]
            for r in [x for x in transitions if x["effective_date"]==date]:
                s,i,a=r["symbol"],r["isin"],r["action"]
                if a=="INCLUSION":
                    if s in proposed: errors.append(f"inclusion already present: {s}")
                    if any(v.isin==i for v in proposed.values()): errors.append(f"inclusion ISIN already present: {i}")
                    proposed[s]=Security(s,r["company_name"],i)
                else:
                    if s not in proposed: errors.append(f"exclusion absent: {s}")
                    else:
                        # An exclusion may carry the historical ISIN that was active
                        # at the index transition; it need not match a later raw-file ISIN.
                        if proposed[s].isin!=i:
                            errors.append(f"exclusion ISIN mismatch for {s}: ledger={i}, current={proposed[s].isin}")
                        del proposed[s]
            dup=[i for i,n in Counter(v.isin for v in proposed.values()).items() if n>1]
            if dup: errors.append("duplicate ISINs: "+",".join(dup))
            expected=51 if date<"2017-09-29" else 50
            if len(proposed)!=expected: errors.append(f"membership count={len(proposed)}, expected {expected}")
            results.append({"effective_date":date,"transition_rows":sum(x["effective_date"]==date for x in transitions),
                            "member_count":len(proposed),"duplicate_isins":";".join(dup),
                            "status":"PASS" if not errors else "FAIL","errors":" | ".join(errors)})
            if errors: break
            members=proposed
        OUT.parent.mkdir(parents=True,exist_ok=True)
        with OUT.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=["effective_date","transition_rows","member_count","duplicate_isins","status","errors"]); w.writeheader(); w.writerows(results)
        failures=[r for r in results if r["status"]=="FAIL"]
        if failures: print("PIT MEMBERSHIP: FAIL\n"+failures[0]["errors"]); return 1
        print(f"Effective states checked: {len(results)}\nPIT MEMBERSHIP: PASS"); return 0
    except RuntimeError as e:
        print(f"PIT MEMBERSHIP: BLOCKED — {e}"); return 2

if __name__=="__main__": raise SystemExit(main())
