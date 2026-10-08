"""Final V6 preflight contract validation.

This module validates only the machine-readable specification. It never runs
performance and never infers a PASS from narrative text.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/phase1a_preregistration.json"

REQUIRED_PRIMARY = {
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

REQUIRED_RULES = {
    "retained_name_rebalancing",
    "retained_name_definition",
    "target_definition",
    "tie_break",
    "nan_signal",
    "missing_signal_price",
    "missing_execution_open",
    "rights_issue",
    "cash_in_lieu",
    "insufficient_eligible_names",
    "unsupported_corporate_action",
    "dividend_timing",
    "p5_is_hard_gate",
}


def validate_contract(config: dict) -> list[str]:
    failures: list[str] = []

    if config.get("frozen_primary") != REQUIRED_PRIMARY:
        failures.append("frozen_primary does not exactly match final V6 contract")

    review_resolution = config.get("review_resolution", {})
    performance_allowed = review_resolution.get("performance_run_allowed")
    if not isinstance(performance_allowed, bool):
        failures.append("performance_run_allowed must be an explicit boolean")
    if performance_allowed is True and review_resolution.get("final_preflight_required") is not True:
        failures.append("performance_run_allowed=true requires final_preflight_required=true")

    if config.get("review_resolution", {}).get("final_preflight_required") is not True:
        failures.append("final_preflight_required must be true")

    rules = config.get("preflight_rules", {})
    for key in sorted(REQUIRED_RULES):
        value = rules.get(key)
        if value in (None, "", [], {}):
            failures.append(f"missing P5 rule: {key}")

    if rules.get("p5_is_hard_gate") is not True:
        failures.append("P5 must be a hard gate")

    random5 = config.get("random5_inference", {})
    if random5.get("p_value_cutoff") != 0.10:
        failures.append("Random-5 one-sided p-value cutoff must be 0.10")
    if random5.get("draws") != 100000:
        failures.append("Random-5 draw count must be 100000")
    if random5.get("seed") != 20261007:
        failures.append("Random-5 seed must be 20261007")

    if config.get("estimand_cost_contract", {}).get(
        "signal_level_fractional_notional", {}
    ).get("fixed_rupee_whole_share_transaction_charges") != "EXCLUDE_AND_REPORT_SEPARATELY":
        failures.append("Estimand A fixed-charge rule is not locked")

    if config.get("primary_inference", {}).get(
        "economic_threshold_annualized_net_excess"
    ) != 0.01:
        failures.append("Estimand B annual threshold must be 0.01")

    if config.get("frozen_primary", {}).get("live_max_cumulative_loss_rs") != 5000:
        failures.append("live maximum cumulative loss must be ₹5,000")

    effect = config.get("effect_size_assumption", {})
    if effect.get("status") != "PRE_RUN_ASSUMPTION_TO_RECOMPUTE":
        failures.append("effect-size assumption must be labeled as pre-run assumption")

    return failures


def main() -> int:
    if not CONFIG.exists():
        print("BLOCKED: missing final V6 configuration")
        return 1

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    failures = validate_contract(config)

    print("PHASE 1A FINAL V6 CONTRACT")
    print(f"Config: {CONFIG}")
    print("Status:", "PASS" if not failures else "BLOCKED")
    for failure in failures:
        print("BLOCKED:", failure)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
