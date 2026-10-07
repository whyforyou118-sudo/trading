"""P6 — fail-closed path-conditional corporate-action census validator."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "audits/phase1a_path_corporate_action_census.csv"
OUT = ROOT / "audits/phase1a_p6_corporate_action_census_report.csv"

REQUIRED = {
    "event_id","event_type","security","event_date","source_reference",
    "supported_by_production_ledger","status"
}


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    if not INPUT.exists():
        print("STATUS: BLOCKED — path-conditional corporate-action census is missing.")
        return 1

    rows = read(INPUT)
    if not rows or not REQUIRED.issubset(rows[0]):
        print("STATUS: BLOCKED — census schema is incomplete.")
        return 1

    failures = []
    for row in rows:
        supported = row["supported_by_production_ledger"].strip().upper()
        status = row["status"].strip().upper()
        if not row["source_reference"].strip():
            failures.append((row["event_id"], "MISSING_SOURCE"))
        elif supported != "TRUE":
            failures.append((row["event_id"], "UNSUPPORTED_EVENT"))
        elif status != "PASS":
            failures.append((row["event_id"], "EVENT_NOT_PASS"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event_id","status","reason"])
        writer.writeheader()
        for event_id, reason in failures:
            writer.writerow({"event_id": event_id, "status": "FAIL", "reason": reason})
        if not failures:
            writer.writerow({"event_id": "ALL", "status": "PASS", "reason": "FAIL_CLOSED_CENSUS_VALIDATED"})

    print("PHASE 1A P6 — CORPORATE-ACTION CENSUS")
    print(f"Events audited: {len(rows)}")
    print(f"Failures: {len(failures)}")
    print(f"Artifact: {OUT}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
