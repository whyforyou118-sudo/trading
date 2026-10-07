# External Reviewer Prompt — Blueprint V6

Review the current Blueprint V6 amendments and repository evidence as a hostile quantitative-research reviewer.

Rules:

1. Quote the exact blueprint sentence/section for every finding. If the cited statement is not present, label the finding INVALID.
2. Distinguish a missing artifact from a methodological flaw.
3. Do not propose changing the frozen primary strategy merely because another universe/parameterization might produce a stronger backtest.
4. Treat NIFTY 50 PIT membership, raw prices, whole-share execution, residual cash, date-effective costs, TRI verification, and sampled corporate-action/PIT reconciliation as existing evidence unless the repository artifact contradicts them.
5. Do not call Phase 0.5 "alpha validation". It is evidence completeness plus documented statistical limitations.
6. Treat the 31-quarter MDE as a limitation. Do not interpret it as an alpha threshold.
7. Evaluate the pre-registered 2023-01-01 to 2025-12-31 holdout as a discipline/sub-period validation, not as a claim that a frozen strategy was trained on 2018-2022.
8. Check that the development-only momentum diagnostic does not inspect holdout returns.
9. Check the equal-target/whole-share/no-replacement rule and its implications for cash drag.
10. Check whether the seven predefined configurations are correctly handled as multiple trials.
11. Check tax, stamp duty, dividend accounting, and transaction-level cost treatment.
12. Separate:
   - CRITICAL methodological errors,
   - MAJOR gaps,
   - MINOR improvements,
   - reviewer misunderstandings.
13. For each valid finding provide:
   - exact quoted text,
   - why it matters,
   - evidence/test required,
   - whether it changes the primary strategy,
   - recommended fix.
14. Do not use "I could not see the artifact" as a methodological criticism when the artifact path is explicitly provided; instead state that the artifact must be supplied to the reviewer.

Final verdict must be one of:
- FREEZE
- FIX THEN FREEZE
- RETHINK

Do not recommend RETHINK merely because a broader universe might have stronger momentum. The primary question is retail-scale PIT NIFTY 50 implementation under realistic frictions.
