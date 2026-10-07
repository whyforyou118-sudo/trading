from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1a_p4_membership_reconciliation import read, START, END


def test_repository_has_42_research_period_transition_rows():
    rows = read(ROOT / "data/reference/nifty50_membership.csv")
    research = [
        r for r in rows
        if START <= r["effective_date"] <= END
    ]
    assert len(rows) == 55
    assert len(research) == 42


def test_research_period_membership_rows_are_officially_sourced():
    rows = read(ROOT / "data/reference/nifty50_membership.csv")
    research = [
        r for r in rows
        if START <= r["effective_date"] <= END
    ]
    assert all(r["source"].strip().upper() == "OFFICIAL" for r in research)
    assert all(r["source_reference"].strip() for r in research)
