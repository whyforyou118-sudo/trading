from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from audit.phase1a_pit import audit_decision_table

def test_future_information_is_rejected(tmp_path: Path):
    p=tmp_path/"decision.csv"
    p.write_text("decision_date,symbol,eligible,available_from,available_to,signal_source_date,execution_date\n2024-01-01,AAA,true,2024-02-01,,2024-01-02,2024-01-02\n",encoding="utf-8")
    codes={x.code for x in audit_decision_table(p)}
    assert {"FUTURE_MEMBERSHIP","FUTURE_SIGNAL","INVALID_EXECUTION_DATE"} <= codes
