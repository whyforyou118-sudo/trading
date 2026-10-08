from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1b_britannia_path_relevance import build_path_relevance_report, _load_rows


def test_frozen_selection_audit_makes_britannia_debenture_events_path_irrelevant():
    rows = _load_rows(ROOT / "audits" / "phase1b_selection_audit.csv")
    report = build_path_relevance_report(rows)

    assert report["status"] == "PASS"
    assert report["run1_authorized"] is False
    assert report["first_BRITANNIA_execution_date"] == "2023-04-03"
    assert report["BRITANNIA_selection_count"] == 1
    assert all(
        event["path_conditionally_irrelevant_to_frozen_V6"]
        for event in report["events"]
    )


def test_path_audit_blocks_if_britannia_was_held_at_entitlement():
    rows = [{
        "decision_date": "2019-06-28",
        "execution_date": "2019-07-01",
        "symbol": "BRITANNIA",
        "selection_status": "PASS",
    }]
    report = build_path_relevance_report(rows)

    assert report["status"] == "BLOCKED"
    assert report["events"][0]["eligible_parent_position_at_ex_date"] is True
    assert report["run1_authorized"] is False


def test_path_audit_blocks_if_ex_date_is_inside_signal_formation_window():
    rows = [{
        "decision_date": "2022-06-25",
        "execution_date": "2022-07-01",
        "symbol": "BRITANNIA",
        "selection_status": "PASS",
    }]
    report = build_path_relevance_report(rows)

    # The 2021 ex-date is within the 12M/1M signal window for this decision.
    event = next(item for item in report["events"] if item["ex_date"] == "2021-05-25")
    assert event["ex_date_in_any_BRITANNIA_signal_formation_window"] is True
    assert event["status"] == "BLOCKED"
    assert report["run1_authorized"] is False
