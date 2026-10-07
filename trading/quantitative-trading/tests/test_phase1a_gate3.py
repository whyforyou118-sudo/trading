from audit.phase1a_gate3_ledger_replays import (
    replay_gail_bonus,
    replay_real_dividend,
    replay_real_tcs_dividend,
    replay_hdfc_merger,
)

def test_real_gail_bonus_replay():
    replay_gail_bonus()

def test_real_gail_dividend_replay():
    replay_real_dividend()

def test_real_tcs_dividend_replay():
    replay_real_tcs_dividend()

def test_real_hdfc_merger_replay():
    replay_hdfc_merger()
