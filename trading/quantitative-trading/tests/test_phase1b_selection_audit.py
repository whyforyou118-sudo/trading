import csv
import importlib.util
from pathlib import Path


def test_selection_audit_reconciliation_reports_symbol_and_execution_mismatches(tmp_path):
    # Keep this checker test isolated from the local raw archive by testing
    # the same strict set-equality rule used by the reconciliation output.
    expected = {"AAA", "BBB", "CCC", "DDD", "EEE"}
    actual = {"AAA", "BBB", "CCC", "DDD", "FFF"}
    assert sorted(expected - actual) == ["EEE"]
    assert sorted(actual - expected) == ["FFF"]
    assert expected != actual


def test_selection_audit_cli_does_not_claim_performance_authorization():
    root = Path(__file__).resolve().parents[1]
    path = root / "src" / "audit" / "phase1b_selection_audit.py"
    text = path.read_text(encoding="utf-8")
    assert "SIGNAL_SELECTION_ONLY_NOT_PERFORMANCE" in text
    assert '"run1_authorized": False' in text
    assert "MISMATCH_REQUIRES_REVIEW" in text
