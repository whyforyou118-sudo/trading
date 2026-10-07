"""Phase 1A Gate 5: preregistered two-estimand and Random-5 inference.

This module defines the inference contract only. It does not run the protected
performance dataset. It keeps the signal-level diagnostic (A) separate from
the frozen ₹25K implementation estimand (B), and defines the exact Random-5
null statistic under the same whole-share/cash rules.
"""
from __future__ import annotations

from dataclasses import dataclass
import random


SEED = 20261007
RANDOM5_DRAWS = 100000
QUARTERLY_THRESHOLD = 0.0025
ANNUAL_THRESHOLD = 0.01


@dataclass(frozen=True)
class EstimandA:
    name: str = "signal_level_top5_vs_random5"
    capital_mode: str = "fractional_notional"
    whole_share: bool = False
    residual_cash: bool = False
    economic_threshold_per_quarter: float = QUARTERLY_THRESHOLD


@dataclass(frozen=True)
class EstimandB:
    name: str = "retail_25000_frozen_implementation"
    capital_rs: int = 25000
    whole_share: bool = True
    residual_cash: bool = True
    economic_threshold_annualized: float = ANNUAL_THRESHOLD


def random5_draw_indices(eligible_count: int, draws: int = RANDOM5_DRAWS, seed: int = SEED):
    if eligible_count < 5:
        raise ValueError("at least five eligible securities are required")
    if draws < 1:
        raise ValueError("draws must be positive")
    rng = random.Random(seed)
    universe = list(range(eligible_count))
    for _ in range(draws):
        yield tuple(sorted(rng.sample(universe, 5)))


def one_sided_plus_one_pvalue(observed: float, null_statistics) -> float:
    null = list(float(x) for x in null_statistics)
    if not null:
        raise ValueError("null_statistics cannot be empty")
    exceed = sum(x >= observed for x in null)
    return (exceed + 1.0) / (len(null) + 1.0)


def classify_estimand_a(mean_net_excess_per_quarter: float, ci_low: float) -> str:
    if ci_low >= QUARTERLY_THRESHOLD:
        return "PASS"
    if mean_net_excess_per_quarter < 0 and ci_low < 0:
        return "FAIL"
    return "INCONCLUSIVE"


def classify_estimand_b(annualized_net_excess_return: float, ci_low: float, inference_pass: bool) -> str:
    if inference_pass and ci_low >= ANNUAL_THRESHOLD:
        return "PASS"
    if annualized_net_excess_return < 0 and ci_low < 0:
        return "FAIL"
    return "INCONCLUSIVE"


def validate_same_null_contract(*, eligible_count: int, unbuyable_replacement: bool,
                                same_execution: bool, same_costs: bool,
                                draws: int = RANDOM5_DRAWS, seed: int = SEED) -> None:
    if eligible_count != 50:
        raise AssertionError("Random-5 universe must be all 50 PIT-eligible names")
    if unbuyable_replacement:
        raise AssertionError("Random-5 must not redraw unbuyable names")
    if not (same_execution and same_costs):
        raise AssertionError("Random-5 must use identical execution and costs")
    if draws != RANDOM5_DRAWS or seed != SEED:
        raise AssertionError("Random-5 draws/seed do not match preregistration")


def main() -> int:
    a, b = EstimandA(), EstimandB()
    validate_same_null_contract(
        eligible_count=50,
        unbuyable_replacement=False,
        same_execution=True,
        same_costs=True,
    )
    draws = random5_draw_indices(50, draws=RANDOM5_DRAWS, seed=SEED)
    first = next(draws)
    print("PHASE 1A GATE 5 — TWO ESTIMANDS / RANDOM-5 CONTRACT")
    print(f"Estimand A: {a}")
    print(f"Estimand B: {b}")
    print(f"Random-5 draws: {RANDOM5_DRAWS}; seed: {SEED}; first draw: {first}")
    print("STATUS: PASS — inference contract validated; no protected performance run executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
