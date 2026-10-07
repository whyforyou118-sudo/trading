# Quantitative Trading Research Rules

## Status

Phase 0 (data feasibility and integrity) has passed locally under the deterministic gate.

The repository is now in **Phase 0.5 — Research Feasibility**. No strategy performance backtest may begin until the Phase 0.5 evidence gate is complete.

No AI-generated PASS statement is evidence by itself.

## Non-negotiable rules

1. Preserve raw market data. Never overwrite or silently transform raw source files.
2. Use stable security identity (ISIN/security ID) rather than ticker symbols as permanent identity.
3. Enforce point-in-time (PIT) NIFTY 50 membership.
4. Never use future information in universe, features, signals, execution, or validation.
5. Executable prices must come from raw exchange data plus an explicit corporate-action/accounting layer; do not silently substitute adjusted Yahoo prices.
6. Corporate actions must live in a canonical, auditable ledger. Never hard-code a one-off price adjustment inside the backtest.
7. All normalization, feature selection, parameter selection, and model fitting must occur only on information available to the relevant research period.
8. Transaction costs, slippage, taxes, integer shares, cash, and execution timing must be explicit.
9. The final holdout must remain technically isolated until the research specification is frozen.
10. Do not delete failed experiments or unfavorable results.
11. Do not change strategy rules, benchmarks, evaluation periods, or success criteria after seeing results without recording a new experiment.
12. AI-generated code must be tested and reviewed.
13. Deterministic data checks must be performed by Python/tests, not narrative judgment.
14. Every important data transformation needs a reproducible test.
15. Do not begin Phase 1A while the Phase 0 gate or Phase 0.5 evidence gate reports FAIL/BLOCKED.
16. Phase 0.5 feasibility calculations must not calculate strategy P&L or select conclusions based on profitability.
17. Missing evidence is a blocker, not a reason to substitute a convenient third-party value.
18. Economic thresholds proposed by reviewers are hypotheses, not universal pass/fail constants; any adopted threshold must be preregistered and justified.

## Frozen primary strategy for later phases

- Universe: NIFTY 50, point-in-time membership.
- Formation: 12 months.
- Skip: 1 month.
- Portfolio: top 5.
- Rebalance: quarterly.
- Target weights: equal 20%.
- Direction: long-only.
- Leverage: none.
- Execution: quarter-end close information, next actual trading day open.
- Primary capital: INR 25,000.
- Capital sensitivity: INR 20,000 / 50,000 / 100,000 / 500,000 / 1,000,000.
- Primary slippage: 0.10%, with sensitivity analysis.
- Benchmarks: NIFTY 50 TRI, NIFTY 50 Price Index, cash, and exposure-matched NIFTY 50 + cash.

Do not change these rules merely because an early feasibility result is inconvenient.

## Phase 0 gate

Phase 0 establishes, at minimum:

- authoritative/reconciled NSE trading calendar,
- complete raw price archive for the declared research period,
- manifest/hash integrity,
- schema/date integrity,
- security identity transitions,
- PIT NIFTY 50 membership,
- PIT price coverage,
- corporate-action coverage/reconciliation.

Any critical FAIL or UNVERIFIED Phase 0 condition blocks Phase 0.5 and later phases.

## Phase 0.5 gate

Phase 0.5 must establish:

- actual quarterly decision count for the declared research period,
- approximate statistical MDE/MDES diagnostic,
- whole-share capital feasibility across all registered capital scenarios,
- unbuyable-selection and target-vs-actual-weight diagnostics,
- verified date-effective Zerodha cost schedule,
- conservative cost-drag feasibility scenario,
- NIFTY 50 TRI data and source verification,
- independent PIT reconciliation for at least five effective dates,
- corporate-action feasibility sample of at least 20 events,
- immutable/traceable audit artifacts.

Phase 0.5 is a **feasibility gate**, not an alpha test.

A complete Phase 0.5 result does not prove that the strategy is profitable, that NIFTY 50 is the optimal universe, or that the statistical sample can detect every plausible effect.

If Phase 0.5 reveals a material design problem, create a new preregistered experiment version before changing the primary design.

## Primary strategy changes

The following are not permitted after performance results are inspected without a new experiment version:

- changing NIFTY 50 to NIFTY 200/500,
- changing Top-5 to another holding count,
- changing quarterly to semiannual/monthly,
- changing the benchmark,
- changing the research period,
- changing cost assumptions to improve results,
- adding a rescue filter,
- removing an unsuccessful variant.

Separate experiments are permitted only when preregistered and reported separately.
