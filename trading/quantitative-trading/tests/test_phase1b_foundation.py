from datetime import date
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data.prices import load_bhavcopy
from strategy.momentum import Member, formation_and_skip_dates, rank_candidates


def test_old_schema_loader(tmp_path):
    raw = b"SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,ISIN,TIMESTAMP\nAAA,EQ,10,11,9,10.5,INEAAA,01-APR-2019\nBBB,GS,20,21,19,20,INEBBB,01-APR-2019\n"
    p = tmp_path / "old.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("cm01APR2019bhav.csv", raw)
    bars = load_bhavcopy(p)
    assert set(bars) == {"AAA"}
    assert bars["AAA"].open == 10
    assert bars["AAA"].date == date(2019, 4, 1)


def test_new_schema_loader(tmp_path):
    raw = b"TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,ISIN,TradDt\nAAA,EQ,10,11,9,10.5,INEAAA,2024-01-02\n"
    p = tmp_path / "new.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("BhavCopy.csv", raw)
    bars = load_bhavcopy(p)
    assert bars["AAA"].close == 10.5
    assert bars["AAA"].date == date(2024, 1, 2)


def test_rank_tie_break_is_symbol_ascending():
    members = {s: Member(s, s, s) for s in ("BBB", "AAA", "CCC")}
    class P:
        def __init__(self, close): self.close = close
    start = {s: P(100) for s in members}
    end = {s: P(110) for s in members}
    ranked = rank_candidates(members, start, end, holdings=3)
    assert [x[0] for x in ranked] == ["AAA", "BBB", "CCC"]
    assert [x[2] for x in ranked] == [1, 2, 3]


def test_frozen_12m_1m_date_mapping():
    ends = {(2024, 2): date(2024, 2, 29), (2025, 1): date(2025, 1, 31), (2025, 2): date(2025, 2, 28)}
    start, end = formation_and_skip_dates(date(2025, 3, 31), ends, 12, 1)
    assert start == date(2024, 2, 29)
    assert end == date(2025, 2, 28)
