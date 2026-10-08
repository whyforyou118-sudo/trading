"""Final P1-P9 preflight aggregator.

This script is intentionally fail-closed. It never runs strategy performance.
P1 and P9 are human/source declarations; P2 requires a separately generated
truncated artifact; P6 requires the path-conditional corporate-action census.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audits/phase1a_preflight_manifest.json"


def run(module: str) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", f"src.audit.{module}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    text = (result.stdout + result.stderr).strip()
    return result.returncode == 0, text[-2000:]


def csv_pass(path: Path, status_column: str = "status") -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return bool(rows) and all(r.get(status_column, "").upper() == "PASS" for r in rows)


def main() -> int:
    checks = []

    p1_ok, p1_text = run("phase1a_p1_spotcheck")
    checks.append({"id":"P1","status":"PASS" if p1_ok else "BLOCKED","detail":p1_text})

    p2_ok, p2_text = run("phase1a_p2_truncation_invariance")
    checks.append({"id":"P2","status":"PASS" if p2_ok else "BLOCKED","detail":p2_text})

    # P3 uses the production accounting module directly.
    try:
        from src.portfolio.accounting import (
            SecurityConversion, Trade, apply_ledger
        )
        state = apply_ledger(0.0, [
            Trade("2020-01-01","HDFC","BUY",25,100.0),
            SecurityConversion("2020-02-01","HDFC","HDFCBANK",42,25),
        ])
        p3_ok = state.shares("HDFC") == 0 and state.shares("HDFCBANK") == 42
        p3_detail = "production SecurityConversion replay passed"
    except Exception as exc:
        p3_ok = False
        p3_detail = repr(exc)
    checks.append({"id":"P3","status":"PASS" if p3_ok else "BLOCKED","detail":p3_detail})

    p4_ok, p4_text = run("phase1a_p4_membership_reconciliation")
    checks.append({"id":"P4","status":"PASS" if p4_ok else "BLOCKED","detail":p4_text})

    # P5 is the machine-readable contract gate.
    p5_ok, p5_text = run("phase1a_preflight_contract")
    checks.append({"id":"P5","status":"PASS" if p5_ok else "BLOCKED","detail":p5_text})

    # The census is intentionally diagnostic: it reports unresolved/special
    # corporate-action rows. P6 passes only when every economically material
    # special row is covered by its explicit treatment audit.
    p6_census_ok, p6_census_text = run("phase1a_p6_corporate_action_census")
    p6_security_ok, p6_security_text = run("phase1a_p6_security_distribution")
    p6_rights_ok, p6_rights_text = run("phase1a_p6_rights_treatment")
    p6_ok = p6_security_ok and p6_rights_ok
    p6_detail = (
        "Census diagnostic:\n" + p6_census_text + "\n"
        + "Security-distribution treatment:\n" + p6_security_text + "\n"
        + "Rights treatment:\n" + p6_rights_text
    )
    checks.append({"id":"P6","status":"PASS" if p6_ok else "BLOCKED","detail":p6_detail})

    # P7 reuses the existing date-effective benchmark/cost reconciliation.
    p7_ok, p7_text = run("phase1a_gate6_benchmark_cost")
    checks.append({"id":"P7","status":"PASS" if p7_ok else "BLOCKED","detail":p7_text})

    p8_ok, p8_text = run("phase1a_p8_dividend_invariant")
    checks.append({"id":"P8","status":"PASS" if p8_ok else "BLOCKED","detail":p8_text})

    p9_ok, p9_text = run("phase1a_p9_execution_source")
    checks.append({"id":"P9","status":"PASS" if p9_ok else "BLOCKED","detail":p9_text})

    overall = all(x["status"] == "PASS" for x in checks)
    manifest = {
        "schema":"phase1a-final-preflight-v1",
        "status":"PASS" if overall else "BLOCKED",
        "performance_run_authorized": overall,
        "checks":checks,
        "note":"This manifest authorizes nothing. Final V6 re-freeze must set performance_run_allowed=true only after this manifest is PASS."
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PHASE 1A FINAL PREFLIGHT")
    for check in checks:
        print(f"{check['id']}: {check['status']}")
    print("STATUS:", manifest["status"])
    print("Manifest:", OUT)
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
