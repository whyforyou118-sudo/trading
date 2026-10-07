"""P4 — reconcile every research-period PIT membership transition.

The repository contains 55 transition rows in total, of which 42 fall inside
the frozen 2018-01-01..2025-12-31 research period. P4 audits exactly those 42.
It does not confuse the 16 announcement/review events with transition count.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMBERSHIP = ROOT / "data/reference/nifty50_membership.csv"
G1 = ROOT / "audits/phase1a_gate1_announcement_effective.csv"
OUT = ROOT / "audits/phase1a_p4_membership_reconciliation.csv"

START = "2018-01-01"
END = "2025-12-31"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def source_key(value: str) -> str:
    # Source strings can contain a filename plus "/ IndexInclExcl.xls".
    token = value.split("/", 1)[0].strip()
    return token


def main() -> int:
    failures = []
    membership = read(MEMBERSHIP)
    reviews = read(G1)

    research = [
        r for r in membership
        if START <= r.get("effective_date", "") <= END
    ]

    review_by_source = {}
    for r in reviews:
        review_by_source[source_key(r["source_reference"])] = r

    output = []
    for row in research:
        ref = source_key(row.get("source_reference", ""))
        review = review_by_source.get(ref)
        status = "PASS"
        reason = "OFFICIAL_SOURCE_RECONCILED"
        if row.get("source", "").strip().upper() != "OFFICIAL":
            status = "FAIL"
            reason = "NON_OFFICIAL_SOURCE"
        elif not row.get("source_reference", "").strip():
            status = "FAIL"
            reason = "MISSING_SOURCE_REFERENCE"
        elif review is None:
            status = "FAIL"
            reason = "MEMBERSHIP_SOURCE_NOT_PRESENT_IN_G1_REVIEW_EVIDENCE"
        elif review.get("status") != "PASS":
            status = "FAIL"
            reason = "LINKED_G1_REVIEW_EVENT_NOT_PASS"

        output.append({
            "effective_date": row["effective_date"],
            "symbol": row["symbol"],
            "action": row["action"],
            "source_reference": row["source_reference"],
            "linked_review_source": ref,
            "status": status,
            "reason": reason,
        })

        if status != "PASS":
            failures.append(output[-1])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output[0].keys())
        writer.writeheader()
        writer.writerows(output)

    print("PHASE 1A P4 — FULL RESEARCH-PERIOD MEMBERSHIP RECONCILIATION")
    print(f"Total membership transitions in repository: {len(membership)}")
    print(f"Research-period transitions: {len(research)}")
    print(f"Expected research-period transitions: 42")
    print(f"Failures: {len(failures)}")
    print(f"Artifact: {OUT}")

    if len(research) != 42:
        print("STATUS: BLOCKED — research-period transition count is not 42.")
        return 1
    if failures:
        for row in failures[:20]:
            print("FAIL:", row)
        print("STATUS: BLOCKED")
        return 1

    print("STATUS: PASS — all 42 research-period transition rows reconcile.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
