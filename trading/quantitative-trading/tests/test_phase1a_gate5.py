from pathlib import Path\nimport sys\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "src"))\n\nfrom audit.phase1a_gate5_two_estimands import (
    EstimandA, EstimandB, classify_estimand_a, classify_estimand_b,
    random5_draw_indices, validate_same_null_contract,
)

def test_two_estimands_are_separate():
    assert EstimandA().whole_share is False
    assert EstimandB().capital_rs == 25000
    assert EstimandB().whole_share is True
    assert EstimandA().percentage_or_notional_costs == "APPLY"
    assert EstimandA().slippage == "APPLY"
    assert EstimandA().fixed_rupee_whole_share_transaction_charges == "EXCLUDE_AND_REPORT_SEPARATELY"

def test_random5_is_deterministic_and_without_replacement():
    a = list(random5_draw_indices(50, 10))
    b = list(random5_draw_indices(50, 10))
    assert a == b
    assert all(len(set(x)) == 5 for x in a)

def test_random5_contract():
    validate_same_null_contract(
        eligible_count=50,
        unbuyable_replacement=False,
        same_execution=True,
        same_costs=True,
    )

def test_inconclusive_is_allowed():
    assert classify_estimand_a(0.002, -0.001) == "INCONCLUSIVE"
    assert classify_estimand_b(0.008, 0.002, 0.20, True) == "INCONCLUSIVE"


def test_estimand_b_pass_requires_economic_and_random5_thresholds():
    assert classify_estimand_b(0.012, 0.004, 0.099, True) == "PASS"
    assert classify_estimand_b(0.012, 0.004, 0.10, True) == "INCONCLUSIVE"


def test_estimand_b_nonpositive_is_fail():
    assert classify_estimand_b(0.0, -0.01, 0.001, True) == "FAIL"
    assert classify_estimand_b(-0.02, -0.01, 0.001, True) == "FAIL"


def test_estimand_b_invalid_implementation_is_fail():
    assert classify_estimand_b(0.05, 0.01, 0.001, False) == "FAIL"
