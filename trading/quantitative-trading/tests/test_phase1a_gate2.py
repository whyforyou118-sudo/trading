from audit.phase1a_gate2_price_invariant import synthetic_split_rank_invariant

def test_split_cannot_create_false_momentum_signal():
    assert synthetic_split_rank_invariant()
