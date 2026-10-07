from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1a_gate4_independent_reproduction import independent_selection


def test_independent_reproduction_has_31_quarters_and_five_ranks():
    rows = independent_selection()
    assert len(rows) == 155
    dates = sorted({r["rebalance_date"] for r in rows})
    assert len(dates) == 31
    for date in dates:
        assert [int(r["rank"]) for r in rows if r["rebalance_date"] == date] == [1, 2, 3, 4, 5]
