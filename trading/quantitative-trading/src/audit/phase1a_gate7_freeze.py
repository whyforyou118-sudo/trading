"""Phase 1A G7 — freeze and performance authorization gate.

This gate never runs a performance backtest. It verifies that the frozen
configuration and required validation artifacts exist, hashes them, records
the current Git commit, and emits a reproducibility manifest. Authorization
is explicit in the emitted manifest; the preregistration itself remains
immutable until this gate passes.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/phase1a_preregistration.json"
OUT = ROOT / "audits/phase1a_g7_freeze_manifest.json"

REQUIRED = [
    "audits/phase1a_gate1_announcement_effective.csv",
    "audits/phase1a_gate3_replay_evidence.csv",
    "audits/phase1a_pit_decision_table.csv",
    "audits/phase1a_pit_report.csv",
    "audits/phase1a_manifest.json",
    "audits/phase05_top5_feasibility.csv",
    "data/reference/zerodha_delivery_cost_schedule.csv",
    "data/reference/nifty50_tri.csv",
    "data/reference/nifty50_equal_weight_tri.csv",
    "audits/phase1a_preflight_manifest.json",
]

EXPECTED_PRIMARY = {
    "universe": "NIFTY_50_PIT",
    "formation_months": 12,
    "skip_months": 1,
    "holdings": 5,
    "rebalance": "quarterly",
    "capital_rs": 25000,
    "execution": "next_actual_trading_day_open",
    "price_mode": "RAW_UNADJUSTED",
    "slippage_pct": 0.1,
    "cost_model": "ZERODHA_DATE_EFFECTIVE",
    "target_weight_pct": 20,
    "direction": "long_only",
    "leverage": "none",
    "cash_return_assumption_pct": 0,
    "unbuyable_policy": "NO_REPLACEMENT_RETAIN_CASH",
    "live_max_cumulative_loss_rs": 5000,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_value(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    failures: list[str] = []
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    if cfg.get("review_resolution", {}).get("performance_run_allowed") is not True:
        failures.append("final re-freeze must explicitly set performance_run_allowed=true")
    if cfg.get("frozen_primary") != EXPECTED_PRIMARY:
        failures.append("frozen_primary does not exactly match the registered V6 primary")
    if cfg.get("primary_unbuyable_policy") != "NO_REPLACEMENT_RETAIN_CASH":
        failures.append("primary_unbuyable_policy mismatch")
    if cfg.get("reproducibility", {}).get("freeze_before_performance_run") is not True:
        failures.append("freeze_before_performance_run must be true")

    hashes = {}
    missing = []
    for rel in REQUIRED:
        path = ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        hashes[rel] = sha256(path)
    if missing:
        failures.extend(f"missing required artifact: {x}" for x in missing)

    if "audits/phase1a_gate1_announcement_effective.csv" in hashes:
        rows = read_csv(ROOT / "audits/phase1a_gate1_announcement_effective.csv")
        if not rows or any(r.get("status") != "PASS" for r in rows):
            failures.append("G1 artifact contains non-PASS rows")
    if "audits/phase1a_preflight_manifest.json" in hashes:
        preflight = json.loads((ROOT / "audits/phase1a_preflight_manifest.json").read_text(encoding="utf-8"))
        if preflight.get("status") != "PASS":
            failures.append("final P1-P9 preflight manifest is not PASS")
        required_checks = {f"P{i}" for i in range(1, 10)}
        reported_checks = {x.get("id") for x in preflight.get("checks", [])}
        if required_checks - reported_checks:
            failures.append("final P1-P9 preflight manifest is incomplete")
    if "audits/phase1a_gate3_replay_evidence.csv" in hashes:
        rows = read_csv(ROOT / "audits/phase1a_gate3_replay_evidence.csv")
        if not rows or any(r.get("status") != "PASS" for r in rows):
            failures.append("G3 replay evidence contains non-PASS rows")
    if "audits/phase1a_pit_report.csv" in hashes:
        rows = read_csv(ROOT / "audits/phase1a_pit_report.csv")
        if any(r.get("code") for r in rows):
            failures.append("PIT audit contains violation rows")
    if "data/reference/nifty50_equal_weight_tri.csv" in hashes:
        rows = read_csv(ROOT / "data/reference/nifty50_equal_weight_tri.csv")
        if not rows:
            failures.append("equal-weight TRI artifact is empty")
        else:
            dates = [r.get("date", "") for r in rows]
            if len(dates) != len(set(dates)):
                failures.append("equal-weight TRI contains duplicate dates")
            if dates[0] > "2018-01-01" or dates[-1] < "2025-12-31":
                failures.append("equal-weight TRI does not cover frozen research period")

    try:
        commit = git_value(["rev-parse", "HEAD"])
        dirty = git_value(["status", "--porcelain"])
    except subprocess.CalledProcessError as exc:
        failures.append(f"git metadata unavailable: {exc}")
        commit, dirty = "", ""

    manifest = {
        "schema": "phase1a-g7-freeze-v1",
        "status": "PASS" if not failures else "BLOCKED",
        "performance_run_authorized": not failures,
        "performance_run_executed": False,
        "git_commit_sha": commit,
        "working_tree_status": "CLEAN" if not dirty else "DIRTY",
        "config_sha256": sha256(CONFIG),
        "frozen_primary": cfg.get("frozen_primary"),
        "required_artifact_sha256": hashes,
        "failures": failures,
        "protected_holdout": cfg.get("decision_dates", {}).get(
            "protected_discipline_holdout_start"
        ) + " through " + cfg.get("decision_dates", {}).get(
            "protected_discipline_holdout_end"
        ),
        "note": "Authorization means validation gates passed; it does not execute performance."
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PHASE 1A GATE 7 — FREEZE / PERFORMANCE AUTHORIZATION")
    print(f"Required artifacts present: {len(hashes)}/{len(REQUIRED)}")
    print(f"Git commit: {commit}")
    print(f"Working tree: {'CLEAN' if not dirty else 'DIRTY'}")
    print(f"Config SHA256: {manifest['config_sha256']}")
    print(f"Performance run executed: False")
    print(f"STATUS: {manifest['status']}")
    if failures:
        for failure in failures:
            print("BLOCKED:", failure)
        return 1
    print("PERFORMANCE RUN AUTHORIZED: YES")
    print(f"Manifest: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
