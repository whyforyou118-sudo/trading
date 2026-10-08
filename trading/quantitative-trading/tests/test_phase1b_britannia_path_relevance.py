from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1b_britannia_path_relevance import build_path_relevance_report, _load_rows


def test_frozen_audit_detects_signal_window_overlap_even_without_a_britannia_holding():
    rows = _load_rows(ROOT / "audits" / "phase1b_selection_audit.csv")
    coverage = _load_rows(
        ROOT / "audits" / "phase1b_selection_coverage.csv",
        {"decision_date", "formation_start", "formation_end"},
    )
    report = build_path_relevance_report(rows, coverage)

    assert report["run1_authorized"] is False
    assert report["formation_window_source"] == "phase1b_selection_coverage.csv"
    assert report["first_BRITANNIA_execution_date"] == "2023-04-03"
    assert report["BRITANNIA_selection_count"] == 1
    assert report["quarterly_decision_dates_checked"] == 31
    assert report["status"] == "BLOCKED"
    assert all(
        event["eligible_parent_position_at_ex_date"] is False
        for event in report["events"]
    )
    assert any(
        event["ex_date_in_any_quarterly_signal_formation_window"]
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
    assert event["ex_date_in_any_quarterly_signal_formation_window"] is True
    assert event["status"] == "BLOCKED"
    assert report["run1_authorized"] is False



def _verified_adjustment_inputs():
    rows = [{
        "decision_date": "2019-09-30",
        "execution_date": "2019-10-01",
        "symbol": "OTHER",
        "selection_status": "PASS",
    }]
    coverage = [
        {
            "decision_date": "2019-09-30",
            "formation_start": "2018-08-31",
            "formation_end": "2019-08-30",
        },
        {
            "decision_date": "2019-12-31",
            "formation_start": "2018-11-30",
            "formation_end": "2019-11-29",
        },
        {
            "decision_date": "2021-06-30",
            "formation_start": "2020-05-29",
            "formation_end": "2021-05-31",
        },
        {
            "decision_date": "2021-09-30",
            "formation_start": "2020-08-31",
            "formation_end": "2021-08-31",
        },
    ]
    event_windows = {
        "BRITANNIA_2019_BONUS_DEBENTURE": ["2019-08-30", "2019-11-29"],
        "BRITANNIA_2021_BONUS_DEBENTURE": ["2021-05-31", "2021-08-31"],
    }
    adjustment_rows = [
        {
            "event_id": event_id,
            "formation_end": formation_end,
            "policy": "provisional_face_value",
            "applied": "True",
            "factor_applied_to_pre_event_equity_prices": "0.99",
        }
        for event_id, formation_ends in event_windows.items()
        for formation_end in formation_ends
    ]
    summary = {
        "status": "PASS",
        "primary_adjustment_status": "PASS",
        "listing_only_sensitivity_status": "PASS",
        "raw_selection_artifact_match": True,
    }
    return rows, coverage, adjustment_rows, summary


def test_path_gate_passes_only_when_all_overlapping_windows_are_adjusted():
    rows, coverage, adjustment_rows, summary = _verified_adjustment_inputs()
    report = build_path_relevance_report(rows, coverage, adjustment_rows, summary)

    assert report["status"] == "PASS"
    assert report["run1_authorized"] is False
    assert all(event["eligible_parent_position_at_ex_date"] is False for event in report["events"])
    assert all(event["signal_effect_resolved_by_primary_adjustment"] for event in report["events"])
    assert all(
        event["path_conditionally_irrelevant_to_frozen_V6"] is False
        for event in report["events"]
    )


def test_path_gate_blocks_if_any_overlapping_window_lacks_adjustment_evidence():
    rows, coverage, adjustment_rows, summary = _verified_adjustment_inputs()
    adjustment_rows = [
        row for row in adjustment_rows
        if not (
            row["event_id"] == "BRITANNIA_2019_BONUS_DEBENTURE"
            and row["formation_end"] == "2019-11-29"
        )
    ]
    report = build_path_relevance_report(rows, coverage, adjustment_rows, summary)

    assert report["status"] == "BLOCKED"
    event = next(
        row for row in report["events"]
        if row["event_id"] == "BRITANNIA_2019_BONUS_DEBENTURE"
    )
    assert event["signal_effect_resolved_by_primary_adjustment"] is False
    assert report["run1_authorized"] is False
