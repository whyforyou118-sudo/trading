from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import mean as arithmetic_mean
from typing import Sequence

@dataclass(frozen=True)
class BootstrapResult:
    estimate: float
    ci_low: float
    ci_high: float
    reps: int
    mean_block_length: int
    seed: int

def _validate(values: Sequence[float]) -> list[float]:
    x = [float(v) for v in values]
    if not x or not all(math.isfinite(v) for v in x):
        raise ValueError("return series must be non-empty and finite")
    return x

def stationary_bootstrap_mean(values: Sequence[float], *, mean_block_length: int = 3, reps: int = 10000, seed: int = 20261007, confidence: float = 0.95) -> BootstrapResult:
    x = _validate(values)
    if mean_block_length < 1 or reps < 1 or not 0 < confidence < 1:
        raise ValueError("invalid bootstrap parameters")
    rng = random.Random(seed)
    n = len(x)
    p = 1.0 / mean_block_length
    estimates = []
    for _ in range(reps):
        sample = []
        while len(sample) < n:
            i = rng.randrange(n)
            while len(sample) < n:
                sample.append(x[i])
                if len(sample) == n or rng.random() < p:
                    break
                i = (i + 1) % n
        estimates.append(arithmetic_mean(sample))
    estimates.sort()
    alpha = 1.0 - confidence
    lo = estimates[max(0, math.floor(alpha * reps / 2) - 1)]
    hi = estimates[min(reps - 1, math.ceil((1 - alpha / 2) * reps) - 1)]
    return BootstrapResult(arithmetic_mean(x), lo, hi, reps, mean_block_length, seed)

def average_ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda z: z[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        r = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = r
        i = j
    return ranks

def spearman_rank_ic(scores: Sequence[float], forward_returns: Sequence[float]) -> float:
    if len(scores) != len(forward_returns) or len(scores) < 2:
        raise ValueError("aligned series of length >= 2 required")
    a, b = average_ranks(scores), average_ranks(forward_returns)
    ma, mb = arithmetic_mean(a), arithmetic_mean(b)
    num = sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den = math.sqrt(sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))
    return float("nan") if den == 0 else num / den

def top_decile_minus_bottom_decile(scores: Sequence[float], forward_returns: Sequence[float]) -> float:
    if len(scores) != len(forward_returns) or len(scores) < 10:
        raise ValueError("at least 10 aligned observations required")
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    k = max(1, len(order) // 10)
    return arithmetic_mean(forward_returns[i] for i in order[-k:]) - arithmetic_mean(forward_returns[i] for i in order[:k])

def random5_permutation_pvalue(scores: Sequence[float], forward_returns: Sequence[float], *, reps: int = 100000, seed: int = 20261007) -> float:
    if len(scores) != len(forward_returns) or len(scores) < 5:
        raise ValueError("at least 5 aligned observations required")
    if reps < 1:
        raise ValueError("reps must be positive")
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    observed = arithmetic_mean(forward_returns[i] for i in order[:5])
    rng = random.Random(seed)
    indices = list(range(len(scores)))
    exceed = sum(arithmetic_mean(forward_returns[i] for i in rng.sample(indices, 5)) >= observed for _ in range(reps))
    return (exceed + 1) / (reps + 1)
