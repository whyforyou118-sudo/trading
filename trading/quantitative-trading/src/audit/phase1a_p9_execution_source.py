"""P9 — validate the explicit historical execution-price source declaration."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "audits/phase1a_p9_execution_price_source.json"


REQUIRED = {
    "source",
    "field",
    "session_convention",
    "availability_convention",
    "missing_open_behavior",
    "suspension_behavior",
    "status",
}


def main() -> int:
    if not INPUT.exists():
        print("STATUS: BLOCKED — execution-price source declaration is missing.")
        return 1
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    missing = sorted(k for k in REQUIRED if not str(data.get(k, "")).strip())
    if missing:
        print("STATUS: BLOCKED — missing:", ", ".join(missing))
        return 1
    if str(data["status"]).upper() != "PASS":
        print("STATUS: BLOCKED — declaration status is not PASS.")
        return 1
    print("PHASE 1A P9 — EXECUTION PRICE SOURCE")
    print(f"Source: {data['source']}")
    print(f"Field: {data['field']}")
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
