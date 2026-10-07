import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from audit.phase1a_preflight_contract import REQUIRED_PRIMARY, REQUIRED_RULES, validate_contract


def load_config():
    return json.loads(
        (ROOT / "config/phase1a_preregistration.json").read_text(encoding="utf-8")
    )


def test_final_v6_primary_contract():
    cfg = load_config()
    assert cfg["frozen_primary"] == REQUIRED_PRIMARY


def test_all_p5_rules_are_explicit_and_hard_gated():
    cfg = load_config()
    rules = cfg["preflight_rules"]
    assert cfg["preflight_rules"]["p5_is_hard_gate"] is True
    assert all(rules.get(key) not in (None, "", [], {}) for key in REQUIRED_RULES)


def test_random5_cutoff_is_frozen():
    cfg = load_config()
    assert cfg["random5_inference"]["p_value_cutoff"] == 0.10
    assert cfg["random5_inference"]["draws"] == 100000
    assert cfg["random5_inference"]["seed"] == 20261007


def test_contract_has_no_unresolved_machine_rules():
    cfg = load_config()
    assert validate_contract(cfg) == []
