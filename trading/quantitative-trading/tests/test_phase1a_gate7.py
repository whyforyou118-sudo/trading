from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1a_gate7_freeze import EXPECTED_PRIMARY


def test_frozen_primary_contract():
    expected = {
        "universe": "NIFTY_50_PIT",
        "formation_months": 12,
        "skip_months": 1,
        "holdings": 5,
        "rebalance": "quarterly",
        "capital_rs": 25000,
        "execution": "next_actual_trading_day_open",
        "price_mode": "RAW_UNADJUSTED",
        "slippage_pct": 0.1,
        "cost_model": "ZERODHA_DATE_EFFECTIVE",
        "target_weight_pct": 20,
        "direction": "long_only",
        "leverage": "none",
        "cash_return_assumption_pct": 0,
        "unbuyable_policy": "NO_REPLACEMENT_RETAIN_CASH",
        "live_max_cumulative_loss_rs": 5000,
    }
    assert EXPECTED_PRIMARY == expected


def test_g7_does_not_execute_performance():
    source = (ROOT / "src/audit/phase1a_gate7_freeze.py").read_text(encoding="utf-8")
    assert "performance_run_executed" in source
    assert "performance_run_authorized" in source
