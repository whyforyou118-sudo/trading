from audit.phase1a_gate5_two_estimands import (
    EstimandA, EstimandB, classify_estimand_a, classify_estimand_b,
    random5_draw_indices, validate_same_null_contract,
)

def test_two_estimands_are_separate():
    assert EstimandA().whole_share is False
    assert EstimandB().capital_rs == 25000
    assert EstimandB().whole_share is True

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
    assert classify_estimand_b(0.008, 0.002, False) == "INCONCLUSIVE"
