from __future__ import annotations
import csv
from datetime import date
from pathlib import Path

def main():
    p=Path(__file__).resolve().parents[2]/"audits/phase1a_gate1_announcement_effective.csv"
    rows=list(csv.DictReader(p.open(encoding="utf-8-sig",newline="")))
    findings=[]
    for i,r in enumerate(rows,2):
        pub=date.fromisoformat(r["publication_date"]); eff=date.fromisoformat(r["effective_date"])
        if not pub < eff:
            findings.append((i,"ANNOUNCEMENT_NOT_BEFORE_EFFECTIVE",r["source_reference"]))
        if r["status"]!="PASS":
            findings.append((i,"SOURCE_ROW_NOT_PASS",r["source_reference"]))
    print("PHASE 1A GATE 1 — ANNOUNCEMENT VS EFFECTIVE DATE")
    print(f"Official review rows: {len(rows)}")
    print(f"Failures: {len(findings)}")
    if findings:
        for x in findings: print(x)
        return 1
    print("STATUS: PASS")
    print("All recorded official NIFTY 50 review/replacement announcements precede their recorded effective dates.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
