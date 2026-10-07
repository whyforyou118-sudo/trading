# V6 Independent Adversarial Review — Phase 1A Freeze

Review target: branch `phase1a-freeze-controls`, commit `8295aecf424f564e560e5c7871bc4327e4d1ae2d`.

This review is against the current V6 amendment and preregistration, not V4/V5.

## Pass A — Statistical / Quantitative Reviewer

### [MAJOR] Holdout remains a discipline sample, not a powered validation set
**Exact source quote:** `The holdout is a discipline device and sub-period validation`.
**Problem:** The 2023–2025 protected period contains only about 11 quarterly decision observations, so it cannot support a strong independent statistical claim.
**Why it matters:** A non-negative holdout is useful for procedural robustness but is weak evidence by itself.
**Correction:** Keep the holdout unchanged but prohibit describing it as a powered confirmation sample. The preregistration already classifies it as a discipline device.
**Changes frozen primary?: NO**
**Already completed?: YES — wording corrected in V6 amendments.**
**Verification artifact:** `config/phase1a_preregistration.json`.

### [MAJOR] Panel/permutation evidence must remain a separate estimand
**Exact source quote:** `The panel/permutation evidence cannot be used to relabel a negative implementable portfolio result as profitable alpha.`
**Problem:** Correctly separated, but implementation must ensure panel returns use the same information timestamp and PIT universe as the actual strategy.
**Correction:** Require date-level universe snapshots, forward-return horizons, and no post-decision membership information in the panel test.
**Changes frozen primary?: NO**
**Already completed?: PARTIAL — specification exists; implementation test remains Phase 1A.**
**Verification artifact:** planned panel/permutation audit.

### [MINOR] Permutation Monte Carlo precision must be reported
**Exact source quote:** `Repeat with a fixed preregistered seed and sufficient repetitions to make the Monte Carlo standard error negligible`.
**Problem:** “Sufficient” is qualitative.
**Correction:** The preregistration now fixes 100,000 repetitions and seed 20261007. Report Monte Carlo standard error for the estimated tail probability.
**Changes frozen primary?: NO**
**Already completed?: YES — preregistered.**
**Verification artifact:** permutation output with seed/repetition count.

### [MINOR] Bootstrap block-length rule is still implementation-specific
**Exact source quote:** `stationary/block bootstrap over the realized portfolio-return sequence`.
**Problem:** The bootstrap family is frozen, but exact block-length selection is not.
**Correction:** Before performance results, choose a deterministic block-length rule based only on the preregistered return-series length/autocorrelation procedure, or preregister a fixed sensitivity grid and report all values.
**Changes frozen primary?: NO**
**Already completed?: NO**
**Verification artifact:** Phase 1A statistical-method configuration/hash.

## Pass B — Data / Implementation Reviewer

### [CRITICAL] No backtest authorization until the transaction/accounting layer exists
**Exact source quote:** `Transaction ledger totals cannot reconcile portfolio cash, holdings, and NAV.`
**Problem:** This is correctly an invalidity rule, but the current branch does not yet contain the actual accounting engine or its reconciliation tests.
**Why it matters:** A mathematically correct strategy specification can still produce invalid returns through share/cash/dividend/corporate-action accounting errors.
**Correction:** Build and test the transaction ledger before Phase 1B performance interpretation.
**Changes frozen primary?: NO**
**Already completed?: NO**
**Verification artifact:** transaction-level ledger + NAV reconciliation test.

### [MAJOR] Corporate-action sample evidence is not completeness
**Exact source quote:** `The 20/20 corporate-action reconciliation is a sample reconciliation, not proof that every corporate action...`
**Problem:** A sampled reconciliation does not prove the historical ledger is complete.
**Correction:** Add targeted invariant/event tests and broader stratified checks before interpreting returns. Do not impose an arbitrary “100 events = pass” rule.
**Changes frozen primary?: NO**
**Already completed?: PARTIAL**
**Verification artifact:** Phase 1A corporate-action test report.

### [MAJOR] PIT sample is not exhaustive
**Exact source quote:** `The 5/5 PIT external reconciliation is a sample.`
**Problem:** Survivorship bias can directly affect historical momentum rankings if a current constituent list is substituted for historical membership.
**Correction:** Run PIT consistency checks over all strategy decision dates, then use external reconciliation as audit evidence rather than as the sole membership proof.
**Changes frozen primary?: NO**
**Already completed?: PARTIAL**
**Verification artifact:** full decision-date PIT reconstruction report.

### [MAJOR] ₹25k implementation is a genuine price-level constraint
**Exact source quote:** `the ₹25,000 implementation is not economically equivalent to an unconstrained equal-weight Top-5 portfolio`.
**Problem:** The no-replacement rule means selection and affordability interact.
**Correction:** Report the actual implementable portfolio separately from an unconstrained signal portfolio, and compare ₹25k with ₹100k as a capital sensitivity.
**Changes frozen primary?: NO**
**Already completed?: PARTIAL — feasibility quantified; performance decomposition remains Phase 1A.**
**Verification artifact:** capital implementation report.

## Pass C — Practical / Research Contribution Reviewer

### [MAJOR] Existing passive momentum products materially change the practical benchmark
**Exact source quote:** `NIFTY200 Momentum 30, Top-5... are future experiments only.`
**Problem:** The project's practical value cannot be judged only against NIFTY 50 TRI. Indian investors already have passive products tracking NIFTY200 Momentum 30.
**Evidence:** NSE's official index page says NIFTY200 Momentum 30 selects 30 high-momentum NIFTY 200 stocks using 6- and 12-month returns adjusted for volatility. citeturn0search0turn0search2 Current products include HDFC NIFTY200 Momentum 30 ETF with a 0.30% base expense ratio and 0.22% 12-month tracking error as of Aug 2026. citeturn0search28 Motilal Oswal's NIFTY200 Momentum 30 Index Fund reports a 0.31% expense ratio and ₹500 minimum application. citeturn0search4
**Correction:** Add a “practical alternatives” comparison to the research discussion. It must not replace the frozen strategy or become a post-result optimization target.
**Changes frozen primary?: NO**
**Already completed?: NO**
**Verification artifact:** dated product-comparison table with official fund/index sources.

### [MINOR] Product comparison must distinguish strategy from benchmark
**Problem:** NIFTY200 Momentum 30 is not the same strategy: it uses NIFTY 200, 6/12-month momentum, volatility adjustment, 30 constituents, factor-tilted weights and buffers. citeturn0search2
**Correction:** Compare economic value, not pretend methodological equivalence.
**Changes frozen primary?: NO**
**Already completed?: NO**
**Verification artifact:** methodology comparison.

## Overall verdict

**FIX THEN FREEZE — no Phase 1 performance backtest yet.**

The V6 freeze is materially stronger than the earlier version. The remaining blockers are implementation/accounting validation and one methodological specification detail: exact deterministic bootstrap block-length selection.

The passive-product comparison is a practical research requirement, not a reason to alter the primary strategy.

### Already completed
- frozen primary strategy;
- equal-target/whole-share/no-replacement rule;
- protected discipline holdout wording;
- preregistered classification;
- portfolio vs panel estimands;
- random-5 permutation design;
- exposure-matched benchmark;
- equal-weight NIFTY 50 secondary benchmark;
- 7-variant registry;
- ₹25k arithmetic requirements.

### Remaining before Phase 1B
1. deterministic bootstrap block-length rule;
2. transaction/NAV accounting engine and invariants;
3. full PIT decision-date consistency check;
4. corporate-action accounting tests;
5. actual panel/permutation implementation;
6. practical passive-product comparison;
7. configuration/data/commit hash manifest.

No result-driven strategy change is justified.
