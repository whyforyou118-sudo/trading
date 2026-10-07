# Blueprint V6 Amendments — Freeze Controls Before Phase 1A

Status: Phase 0.5 evidence complete; Blueprint V6 controls frozen on branch `phase05-research-feasibility`.

## 1. Statistical power terminology

Replace "Statistical feasibility PASS" with **Statistical power assessment — DOCUMENTED LIMITATION**.

The current planning diagnostic is approximately 31 eligible quarterly decisions, MDE Sharpe ≈ 0.4707 and annualized excess-return MDE ≈ 9.41% under the Phase 0.5 assumptions. This does **not** mean the study is adequately powered. It means the limitation is quantified.

Phase 1 inference must use the realized return series and dependence-aware methods. DSR/Reality Check/SPA are diagnostics for research-selection effects, not proof that alpha exists.

## 2. Primary strategy remains frozen

Do not change the primary universe or parameters in response to reviewer suggestions.

- PIT NIFTY 50
- 12-month formation
- 1-month skip
- Top 5
- Quarterly rebalance
- Long-only
- No leverage
- ₹25,000 primary capital
- Next actual trading-day open execution
- Raw/unadjusted executable prices
- Primary slippage 0.10%
- Zerodha primary cost model

NIFTY 200/500, Top-10/15, or other universes are future experiments only.

## 3. Portfolio-weight definition

The strategy is **equal-target**, not guaranteed equal-weight after execution.

Each selected stock has a 20% target. Whole-share execution determines actual weights and residual cash.

Unbuyable rule:

> Do not replace an unbuyable selected stock with the next-ranked stock. Allocate zero shares for that selected name and retain the intended capital as cash.

If fewer than five stocks are eligible:

> Hold all eligible stocks and retain the remaining target capital as cash.

These rules are frozen before performance backtesting.

## 4. Protected holdout

Pre-registered holdout:

- Development: 2018-01-01 through 2022-12-31
- Protected holdout: 2023-01-01 through 2025-12-31

The holdout is a discipline device and sub-period validation, not a claim that the primary frozen strategy was "trained" on development data.

Pre-holdout observations may be used for signal warm-up. Holdout returns must not be used to modify strategy parameters, benchmarks, cost assumptions, or success criteria.

## 5. Momentum diagnostic

Before Phase 1B performance interpretation, run a development-only diagnostic on the PIT NIFTY 50:

- 12M/1M momentum ranking
- rank information coefficient (Rank IC)
- top-decile minus bottom-decile spread
- development period only: 2018-01-01 through 2022-12-31

Do not use the protected holdout for this diagnostic.

This diagnostic is not the primary strategy and does not authorize changing the primary universe or parameters.

## 6. Multiple testing

Seven configurations are pre-registered:

1. 12/1/5 quarterly primary
2. 6/1/5
3. 9/1/5
4. 12/0/5
5. 12/1/3
6. 12/1/10
7. 12/1/5 monthly

If all seven are evaluated, all seven count toward multiple-testing diagnostics.

## 7. Corporate-action evidence wording

The 20/20 corporate-action reconciliation is a **sample reconciliation**, not proof that every corporate action in the historical universe has been independently verified.

The artifact is:

`audits/phase05_corporate_action_reconciliation.csv`

Completeness remains an implementation risk to be tested by Phase 1A accounting and targeted event tests.

## 8. PIT evidence wording

The 5/5 PIT external reconciliation is a sample.

It demonstrates that sampled historical constituent transitions agree with the local PIT ledger. It is not a claim that every NIFTY 50 reconstitution has independently been reconciled.

Phase 1A must add broader PIT consistency checks before performance interpretation.

## 9. Dividend invariant

Primary price mode is RAW_UNADJUSTED.

Therefore:

- raw prices do not embed dividends;
- dividends are credited separately as cash;
- adjusted-price series must never be combined with separate dividend cash credits.

The implementation must include an invariant/unit test preventing accidental double counting.

## 10. Costs

The Zerodha schedule is date-effective and verified for the declared research interval.

Phase 1 performance must report each cost component separately:

- brokerage
- STT
- exchange transaction charges
- SEBI charge
- GST
- stamp duty
- DP charge
- slippage

Phase 0.5 cost feasibility is a conservative 100%-liquidate-and-rebuild scenario. It is not a claim that realized quarterly turnover will equal 100%.

Realized turnover and actual cost drag must be reported once the transaction ledger exists.

## 11. Stamp duty

Pre-July-2020 stamp duty is state-dependent. The primary research assumption is the documented state-agnostic sensitivity anchor already present in the verified schedule.

It must remain explicitly labeled as a sensitivity assumption, not universal historical fact.

## 12. Tax

Primary strategy performance is reported before personal income tax because individual tax classification depends on the investor's circumstances.

Separate tax scenarios are versioned in:

`data/reference/india_equity_tax_schedule.csv`

The capital-gains schedule distinguishes the pre/post 23-Jul-2024 special rates. Business-income treatment remains a separate scenario.

## 13. Paper trading

Paper trading validates operational behavior:

- signal generation
- order generation
- broker/API integration
- position reconciliation
- cash reconciliation
- duplicate-order prevention
- error handling

Paper trading does not validate actual exchange fills, queue position, market impact, or the 0.10% slippage assumption.

Slippage therefore remains a backtest assumption and is stress-tested at 0.05%, 0.10%, 0.20%, and 0.50%.

## 14. Statistical interpretation

A negative eight-year result after costs is descriptive evidence for this implementation and sample path; it is not proof that Indian momentum has zero expected alpha.

A positive result is not sufficient either.

The result must be classified as:

- robust evidence
- moderate evidence
- weak/fragile evidence
- failure
- inconclusive

The documented MDE means that modest effects may remain statistically indistinguishable from noise.

## 15. Phase 0.5 evidence status

Verified:

- statistical power limitation documented
- Top-5 capital feasibility artifact
- Zerodha date-effective cost schedule
- NIFTY 50 TRI source/data and five-date verification
- five PIT external reconciliation rows
- 20 corporate-action reconciliation rows

The evidence-complete gate authorizes Phase 1A. It does not establish alpha.

## 16. Required Phase 1A proof artifacts

Before performance interpretation, produce:

1. implementation/unit-test report;
2. exact integer-share and residual-cash report;
3. transaction-level cost report;
4. dividend accounting invariant test;
5. corporate-action accounting tests;
6. PIT consistency report;
7. development-only Rank IC/top-bottom-decile diagnostic;
8. dependence-aware statistical report;
9. experiment registry containing all seven predefined configurations;
10. protected-holdout configuration hash.

No result-driven changes to the frozen primary strategy are permitted.


## 17. ₹25,000 capital-constrained implementation evidence

The deterministic Phase 0.5 reconstruction uses the actual 155-row Top-5 feasibility artifact and the frozen equal-target/whole-share/no-replacement rules.

Results across 31 executable rebalances:

| Capital | Unbuyable rebalances | Unbuyable slots | Mean cash | Median cash | Max cash | Mean invested | Mean abs. weight deviation |
|---:|---:|---:|---:|---:|---:|---:|---:|
| ₹20,000 | 21/31 (67.74%) | 26 | 26.43% | 26.66% | 52.79% | 73.57% | 5.29% |
| ₹25,000 | 19/31 (61.29%) | 22 | 24.91% | 25.82% | 56.85% | 75.09% | 4.98% |
| ₹50,000 | 7/31 (22.58%) | 7 | 13.05% | 10.74% | 30.11% | 86.95% | 2.61% |
| ₹100,000 | 0/31 | 0 | 5.34% | 4.94% | 12.56% | 94.66% | 1.07% |
| ₹500,000 | 0/31 | 0 | 1.17% | 0.90% | 3.46% | 98.83% | 0.23% |
| ₹1,000,000 | 0/31 | 0 | 0.55% | 0.39% | 1.62% | 99.45% | 0.11% |

Artifact:

`audits/phase05_retail_friction_report.csv`

These are deterministic implementation-feasibility results, not strategy performance results.

### Capital/price-level constraint disclosure

At ₹25,000, whole-share execution can cause a selected high-price constituent to receive zero shares. The primary rule does not replace that constituent with a lower-ranked stock. The intended allocation remains cash.

Therefore the ₹25,000 implementation is not economically equivalent to an unconstrained equal-weight Top-5 portfolio. It contains a real capital/price-level implementation constraint that can interact with security selection.

This is an intended consequence of the frozen retail implementation, not a reason to alter the primary strategy after observing results.

### Cost interpretation

The Phase 0.5 conservative ₹25,000 cost scenario is 2.97% modeled drag under a full-liquidation/rebuild assumption. It is not realized strategy turnover and is not itself the strategy's final break-even return.

Phase 1 must calculate actual transaction-level turnover and realized cost drag. Residual cash must be treated separately from transaction costs because cash is an exposure/opportunity-cost effect, not a transaction charge.

## 18. Phase 1A preregistered inference and classification rules

The following rules are frozen before any Phase 1 performance result is inspected. They are classification rules, not optimization targets.

### 18.1 Primary performance question

The primary portfolio question is:

> Does the frozen ₹25,000, PIT NIFTY 50, 12M/1M, Top-5, quarterly strategy produce positive economically meaningful excess return versus the NIFTY 50 TRI after transaction costs, slippage, dividends, integer-share execution, and residual cash?

The primary comparison is against NIFTY 50 TRI. The NIFTY 50 Price Index, cash, and exposure-matched NIFTY 50 + cash remain secondary benchmarks.

### 18.2 Exposure-matched benchmark

For each portfolio valuation interval, let (w_t) be the strategy's invested-equity weight and (1-w_t) its cash weight.

The exposure-matched benchmark return is:

`R^{EM}_t = w_t R^{TRI}_t + (1-w_t)R^{cash}_t`

The primary cash return assumption is 0% unless a separately preregistered cash-rate experiment is run. The benchmark therefore isolates stock-selection/implementation performance from the mechanical effect of holding less than 100% equity exposure.

A separate equal-weight NIFTY 50 benchmark is added as a secondary diagnostic and does not replace NIFTY 50 TRI.

### 18.3 Cross-sectional information question

The panel question is separate from the portfolio question:

> Does the frozen 12M/1M momentum ranking contain cross-sectional information about subsequent returns within the PIT NIFTY 50 universe?

Required statistics:

- date-by-date Rank IC between momentum score and subsequent forward return;
- top-decile minus bottom-decile spread where the eligible cross-section supports the deciles;
- date-stratified permutation test for the Top-5 mean forward return;
- random-5-stock null distribution using the same eligible PIT universe, date, holding horizon, and portfolio size.

The panel/permutation evidence cannot be used to relabel a negative implementable portfolio result as profitable alpha.

### 18.4 Permutation test

For each eligible decision date, retain the exact PIT-eligible universe and forward-return horizon. Under the null, randomly select five eligible securities without replacement and calculate the same equal-target, unconstrained signal-return statistic used by the cross-sectional test.

Repeat with a fixed preregistered seed and sufficient repetitions to make the Monte Carlo standard error negligible relative to the p-value decision. The observed Top-5 statistic is compared with the pooled date-stratified null distribution.

The permutation procedure must not use future membership information, and it must not replace the actual portfolio implementation test.

### 18.5 Dependence-aware portfolio inference

Portfolio-return inference must use a dependence-aware resampling method rather than relying only on iid Gaussian assumptions.

Primary method:

- stationary/block bootstrap over the realized portfolio-return sequence;
- resample complete return intervals, not individual stock observations;
- preserve the chronological return structure within each sampled block;
- report the bootstrap distribution and two-sided 95% interval for excess return versus NIFTY 50 TRI.

DSR, White Reality Check, and Hansen SPA are secondary research-selection diagnostics when their assumptions are met.

### 18.6 Preregistered result classification

Use the following decision tree after all preregistered calculations are complete:

**Robust evidence**
- primary excess return after all modeled costs is positive;
- the dependence-aware 95% bootstrap interval for primary excess return excludes zero on the positive side;
- the protected discipline holdout cumulative excess return is non-negative;
- at least 5 of the 7 preregistered configurations have positive excess return;
- the cross-sectional Top-5 permutation test rejects the random-5 null at two-sided alpha = 0.05.

**Moderate evidence**
- primary excess return is positive;
- at least 4 of 7 configurations have positive excess return;
- the evidence is directionally positive but at least one robust-evidence requirement above is not met;
- no data/accounting invariant fails.

**Weak/fragile evidence**
- the primary result is positive but fewer than 4 of 7 configurations are positive, or the result is materially dependent on one implementation/cost assumption;
- or the cross-sectional and portfolio evidence disagree.

**Failure**
- primary excess return is non-positive after costs and at least 5 of 7 configurations are non-positive;
- and the permutation test does not reject the random-5 null at alpha = 0.05.

**Inconclusive**
- any case not meeting the definitions above, including insufficient/invalid data, unresolved accounting defects, or evidence that is too weak to distinguish the observed result from noise.

A classification of failure or inconclusive is not a claim that momentum has zero expected alpha in the wider market.

### 18.7 Kill/invalidity rules

Stop the performance interpretation and return to implementation validation if any of the following occurs:

1. PIT membership cannot be reconstructed for a required decision date.
2. Raw-price/dividend accounting invariant fails.
3. Corporate-action accounting produces an unexplained share/cash discontinuity.
4. Transaction ledger totals cannot reconcile portfolio cash, holdings, and NAV.
5. Execution timing uses a price unavailable at the decision timestamp.
6. A protected-holdout value is found to have influenced a strategy/configuration decision before the final classification.
7. A preregistered experiment configuration cannot be reproduced from its recorded hash/commit.

These are validity failures, not negative-alpha results.

### 18.8 ₹25,000 implementation disclosure

The primary ₹25,000 result must report separately:

- unbuyable selected-stock frequency;
- number of unbuyable slots;
- mean/median/max residual cash;
- mean invested exposure;
- mean absolute target-weight deviation;
- actual transaction costs;
- actual slippage;
- gross return before implementation frictions;
- net return after implementation frictions.

The ₹100,000 scenario is the first capital sensitivity with zero unbuyable rebalances in the Phase 0.5 feasibility artifact. It is a sensitivity diagnostic, not a replacement primary capital.

### 18.9 Break-even definition

Break-even must be reported in two distinct forms:

1. **Transaction-cost break-even:** the minimum gross strategy return required to offset realized transaction costs and slippage, holding the realized portfolio exposure path fixed.
2. **Capital-constrained economic break-even:** the minimum gross stock-selection return required for the actual ₹25,000 portfolio, including residual-cash drag, to match the selected benchmark.

Residual cash must never be counted as a transaction cost.

### 18.10 Multiple-testing and reproducibility

All seven preregistered configurations are fixed before performance execution. Their names, parameters, code version, configuration hash, data hashes, random seeds, and Git commit SHA must be recorded.

No additional strategy variant may be promoted into the primary result table after results are observed.

The complete Phase 1A preregistration is stored in `config/phase1a_preregistration.json` and must be hashed/committed before the first Phase 1 performance run.

## 19. Deterministic bootstrap rule

The primary portfolio inference uses a stationary bootstrap with a fixed mean block length of **3 portfolio-return intervals**, corresponding to the quarterly primary strategy's short return history.

For the monthly robustness variant, use the same calendar-time principle by setting the mean block length to 3 monthly observations. No block length may be selected after observing performance.

The report must include a sensitivity check at mean block lengths 2, 3, and 4. This sensitivity is a statistical robustness diagnostic only; it does not create additional strategy variants.

The random-number seed for bootstrap resampling is fixed at **20261007**. The number of bootstrap replications is fixed at **10,000**.


