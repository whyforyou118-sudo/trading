from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

@dataclass(frozen=True)
class PITFinding:
    row: int
    code: str
    detail: str

def _d(value: str) -> date:
    return date.fromisoformat(value)

def audit_decision_table(path: Path) -> list[PITFinding]:
    required = {"decision_date","symbol","eligible","available_from","available_to","signal_source_date","execution_date"}
    findings=[]
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader=csv.DictReader(f)
        missing=required-set(reader.fieldnames or [])
        if missing: raise ValueError(f"missing required PIT fields: {sorted(missing)}")
        for row_no,row in enumerate(reader,start=2):
            try:
                decision=_d(row["decision_date"]); start=_d(row["available_from"])
                end=_d(row["available_to"]) if row["available_to"] else None
                source=_d(row["signal_source_date"]); execution=_d(row["execution_date"])
            except ValueError as exc:
                findings.append(PITFinding(row_no,"INVALID_DATE",str(exc))); continue
            if row["eligible"].strip().lower() not in {"true","1","yes"}: continue
            if decision < start: findings.append(PITFinding(row_no,"FUTURE_MEMBERSHIP",row["symbol"]))
            if end is not None and decision > end: findings.append(PITFinding(row_no,"EXPIRED_MEMBERSHIP",row["symbol"]))
            if source > decision: findings.append(PITFinding(row_no,"FUTURE_SIGNAL",row["symbol"]))
            # Execution must occur after both the decision date and the
            # signal source date. This prevents same-day execution from
            # consuming information that is only available at that date.
            if execution <= decision or execution <= source:
                findings.append(PITFinding(row_no,"INVALID_EXECUTION_DATE",row["symbol"]))
    return findings

if __name__ == "__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("decision_table",type=Path); ap.add_argument("--report",type=Path,required=True)
    a=ap.parse_args(); findings=audit_decision_table(a.decision_table)
    with a.report.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["row","code","detail"]); w.writerows((x.row,x.code,x.detail) for x in findings)
    raise SystemExit(1 if findings else 0)
