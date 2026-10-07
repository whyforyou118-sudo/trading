from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1a_gate6_benchmark_cost import coverage_check
from data.download_nifty50_equal_weight_tri import INDEX_NAME


def test_cost_schedule_covers_frozen_period_without_gaps():
    rows = [
        {"effective_from":"2018-01-01","effective_to":"2020-06-30","verified":"TRUE","source_reference":"x","stamp_basis":"STATE_AGNOSTIC_SENSITIVITY_ANCHOR"},
        {"effective_from":"2020-07-01","effective_to":"2025-12-31","verified":"TRUE","source_reference":"x","stamp_basis":"UNIFORM_STATUTORY_RATE"},
    ]
    intervals, failures = coverage_check(rows)
    assert len(intervals) == 2
    assert failures == []


def test_equal_weight_benchmark_uses_official_index_name():
    assert INDEX_NAME == "Nifty50 Equal Weight"
