# Adversarial Panel Prompt — Blueprint V6 / Phase 1A Freeze

## Version and materials

Review the **current Blueprint V6 / Phase 1A freeze controls**, not an earlier V4/V5 draft.

Primary repository branch under review:

`phase1a-freeze-controls`

Required materials to attach before each review session:

1. the complete current Blueprint V6 document;
2. `docs/BLUEPRINT_V6_AMENDMENTS.md`;
3. `config/phase1a_preregistration.json`;
4. Phase 0/0.5 audit artifacts that are actually available;
5. the exact Git commit SHA being reviewed.

Completed evidence must be treated as completed evidence, not regenerated as an imaginary to-do. Reviewers must distinguish:
- **completed evidence**;
- **documented limitation**;
- **remaining Phase 1A proof obligation**.

## Frozen-primary rule

The primary strategy is frozen:

- PIT NIFTY 50;
- 12M formation / 1M skip;
- Top-5;
- quarterly rebalance;
- long-only;
- no leverage;
- ₹25,000 primary capital;
- next actual trading-day open;
- raw/unadjusted executable prices;
- 0.10% primary slippage;
- Zerodha primary cost model.

Alternative universes, holding counts, frequencies, or rescue filters may be discussed only as separate future experiments. They must **not** be proposed as replacements for the frozen primary strategy.

Alternatives are for deciding whether the project is worth running, not for silently replacing the primary strategy.

## Review discipline

Every finding must include:

1. severity: CRITICAL / MAJOR / MINOR / INFO;
2. exact blueprint quote or exact repository path + quoted text supporting the finding;
3. why the quoted text creates the defect;
4. a concrete correction;
5. whether the correction changes the frozen primary strategy;
6. whether the issue is already completed in Phase 0/0.5;
7. verification evidence required.

If the source does not support a claimed fact, write **[UNVERIFIED]**. Never fabricate a source, count, section, artifact, URL, or result.

For every external source:
- provide the URL;
- provide access date;
- distinguish source fact from inference.

Do not review a summary instead of the document. Review the actual document at section level.

## Statistical-power requirement

For every power criticism, show arithmetic:

- number of observations (n);
- assumed or realized volatility;
- alpha;
- target power;
- correlation/dependence assumption where relevant;
- formula used;
- resulting MDE or detectable effect;
- whether the calculation applies to portfolio returns or the cross-sectional panel.

Do not claim that a 31-observation portfolio series is high-powered.

Review both:
1. portfolio-level inference with dependence-aware bootstrap;
2. higher-observation cross-sectional Rank IC / decile / permutation tests.

Do not use the panel tests to pretend that the portfolio-level test has more observations than it actually has.

## ₹25k implementation requirement

Explicitly calculate/report:

- target amount per stock = ₹25,000 / 5 = ₹5,000;
- frequency with which ₹5,000 cannot buy one whole share of a selected stock;
- unbuyable rebalances;
- unbuyable slots;
- mean/median/max residual cash;
- mean invested exposure;
- conservative and realized transaction costs when available;
- transaction-cost break-even;
- capital-constrained economic break-even.

Residual cash is not a transaction cost.

## Review areas

A. Data/PIT/survivorship  
B. Corporate actions/dividends/accounting  
C. Strategy specification and execution  
D. ₹25k implementation feasibility  
E. Statistical power and inference  
F. Panel/permutation design  
G. Multiple testing and preregistration  
H. Benchmark construction  
I. Costs/taxes/slippage  
J. Holdout integrity  
K. Reproducibility/hash/commit controls  
L. Paper-trading operational claims  
M. Practical value versus available passive momentum products  
N. Publication/research contribution  
O. Live-trading governance

## Required output

For each finding, use:

### [SEVERITY] Finding
**Exact source quote:**  
**Problem:**  
**Why it matters:**  
**Correction:**  
**Changes frozen primary?: YES/NO**  
**Already completed?: YES/NO**  
**Verification artifact:**  

Finish with:

1. findings that genuinely block Phase 1A;
2. findings that are documentation only;
3. findings already completed;
4. findings that would require a new experiment rather than a blueprint correction;
5. final verdict: **FREEZE / FIX THEN FREEZE / DO NOT PROCEED**.

The panel must not invent defects by reviewing an earlier version.
