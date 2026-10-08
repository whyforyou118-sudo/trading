from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1b_britannia_debenture_price_audit import parse_debenture_rows


def test_parses_legacy_bhavcopy_debenture_by_isin():
    raw = (
        "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,TIMESTAMP,ISIN\n"
        "BRITANNIA,N3,29.5,30,29,29.8,09-Oct-2019,INE216A07052\n"
        "BRITANNIA,EQ,3000,3050,2990,3020,09-Oct-2019,INE216A01030\n"
    ).encode()
    rows = parse_debenture_rows(raw, "legacy.csv")
    assert len(rows) == 1
    assert rows[0]["isin"] == "INE216A07052"
    assert rows[0]["date"] == "2019-10-09"
    assert rows[0]["series"] == "N3"
    assert float(rows[0]["open"]) == pytest.approx(29.5)


def test_parses_new_bhavcopy_debenture_by_isin():
    raw = (
        "TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,TradDt,ISIN\n"
        "BRITANNIA,N4,28.5,29,28,28.8,2021-07-20,INE216A08027\n"
    ).encode()
    rows = parse_debenture_rows(raw, "new.csv")
    assert len(rows) == 1
    assert rows[0]["isin"] == "INE216A08027"
    assert rows[0]["date"] == "2021-07-20"
    assert float(rows[0]["close"]) == pytest.approx(28.8)


def test_ignores_equity_and_unrelated_debt_isins():
    raw = (
        "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,TIMESTAMP,ISIN\n"
        "BRITANNIA,EQ,5000,5050,4990,5020,09-Oct-2019,INE216A01030\n"
        "OTHER,N1,100,101,99,100,09-Oct-2019,INE000A00000\n"
    ).encode()
    assert parse_debenture_rows(raw) == []


def test_unknown_schema_fails_closed():
    with pytest.raises(ValueError, match="unknown NSE bhavcopy schema"):
        parse_debenture_rows(b"symbol,price\nBRITANNIA,30\n")

def test_parses_two_digit_year_legacy_nse_date():
    raw = (
        "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,TIMESTAMP,ISIN\n"
        "BRITANNIA,N3,29.5,30,29,29.8,13-Jul-20,INE216A07052\n"
    ).encode()
    rows = parse_debenture_rows(raw, "legacy-two-digit-year.csv")
    assert len(rows) == 1
    assert rows[0]["date"] == "2020-07-13"
