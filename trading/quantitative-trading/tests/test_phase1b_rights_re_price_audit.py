from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit.phase1b_rights_re_price_audit import read_rows


def test_reads_target_rights_entitlement_from_legacy_bhavcopy(tmp_path):
    path = tmp_path / "legacy.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["SYMBOL", "SERIES", "OPEN", "TIMESTAMP"]
        )
        writer.writeheader()
        writer.writerow({
            "SYMBOL": "GRASIM-RE", "SERIES": "BE", "OPEN": "321.5",
            "TIMESTAMP": "17-Jan-2024",
        })
        writer.writerow({
            "SYMBOL": "GRASIM", "SERIES": "EQ", "OPEN": "2100",
            "TIMESTAMP": "17-Jan-2024",
        })
    rows = read_rows(path)
    assert rows == [{
        "date": "2024-01-17",
        "symbol": "GRASIM-RE",
        "series": "BE",
        "open": "321.5",
        "source_file": "legacy.csv",
    }]


def test_reads_target_rights_entitlement_from_new_bhavcopy(tmp_path):
    path = tmp_path / "new.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["TckrSymb", "SctySrs", "OpnPric", "TradDt"]
        )
        writer.writeheader()
        writer.writerow({
            "TckrSymb": "TATACON-RE", "SctySrs": "BE", "OpnPric": "88.25",
            "TradDt": "2024-08-05",
        })
    rows = read_rows(path)
    assert rows[0]["date"] == "2024-08-05"
    assert rows[0]["symbol"] == "TATACON-RE"
    assert rows[0]["series"] == "BE"
    assert rows[0]["open"] == "88.25"


def test_ignores_non_target_symbol_and_date(tmp_path):
    path = tmp_path / "other.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["SYMBOL", "SERIES", "OPEN", "TIMESTAMP"]
        )
        writer.writeheader()
        writer.writerow({
            "SYMBOL": "GRASIM-RE", "SERIES": "BE", "OPEN": "321.5",
            "TIMESTAMP": "18-Jan-2024",
        })
    assert read_rows(path) == []
