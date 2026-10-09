"""Regression tests for fail-closed Phase 1A P6 aggregation."""
import json

from src.audit import phase1a_preflight_manifest as manifest


def test_unresolved_census_blocks_p6_and_authorization(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "OUT", tmp_path / "phase1a_preflight_manifest.json")
    results = {
        "phase1a_p1_spotcheck": (True, "P1 pass"),
        "phase1a_p2_truncation_invariance": (True, "P2 pass"),
        "phase1a_p4_membership_reconciliation": (True, "P4 pass"),
        "phase1a_preflight_contract": (True, "P5 pass"),
        "phase1a_p6_corporate_action_census": (False, "unresolved corporate-action census"),
        "phase1a_p6_security_distribution": (True, "security distribution pass"),
        "phase1a_p6_rights_treatment": (True, "rights treatment pass"),
        "phase1a_gate6_benchmark_cost": (True, "P7 pass"),
        "phase1a_p8_dividend_invariant": (True, "P8 pass"),
        "phase1a_p9_execution_source": (True, "P9 pass"),
    }
    monkeypatch.setattr(manifest, "run", lambda module: results[module])

    assert manifest.main() == 1
    payload = json.loads(manifest.OUT.read_text(encoding="utf-8"))
    assert payload["status"] == "BLOCKED"
    assert payload["performance_run_authorized"] is False
    p6 = next(check for check in payload["checks"] if check["id"] == "P6")
    assert p6["status"] == "BLOCKED"
    assert "unresolved corporate-action census" in p6["detail"]
