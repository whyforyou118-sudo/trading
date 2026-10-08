"""P8 — validate real dividend replay evidence and ex-date convention."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "audits/phase1a_gate3_replay_evidence.csv"
OUT = ROOT / "audits/phase1a_p8_dividend_invariant.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    if not EVIDENCE.exists():
        print("STATUS: BLOCKED — G3 dividend evidence is missing.")
        return 1

    rows = [
        r for r in read(EVIDENCE)
        if r.get("event_type", "").strip().upper() == "DIVIDEND"
    ]
    failures = []
    for row in rows:
        if row.get("status") != "PASS":
            failures.append(f"{row.get('event_id')}: replay status is not PASS")
        if not row.get("ex_date", "").strip():
            failures.append(f"{row.get('event_id')}: ex_date missing")
        if not row.get("record_date", "").strip():
            failures.append(f"{row.get('event_id')}: record_date missing")
        if "cash credited" not in row.get("note", "").lower():
            failures.append(f"{row.get('event_id')}: cash-credit evidence missing")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check","status","detail"])
        writer.writeheader()
        writer.writerow({
            "check":"real_dividend_replay",
            "status":"PASS" if rows and not failures else "FAIL",
            "detail":f"{len(rows)} real dividend replay rows checked"
        })

    print("PHASE 1A P8 — DIVIDEND INVARIANT")
    print(f"Dividend evidence rows: {len(rows)}")
    print(f"Failures: {len(failures)}")
    if failures:
        for x in failures:
            print("BLOCKED:", x)
        return 1
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
