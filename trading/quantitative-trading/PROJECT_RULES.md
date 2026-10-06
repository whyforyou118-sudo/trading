# Quantitative Trading Research Rules

## Status

This repository is a research system. Phase 0 (data feasibility and integrity) is not yet passed.

No strategy backtest, performance claim, or live-trading decision may be treated as valid until the Phase 0 gate passes.

## Non-negotiable rules

1. Preserve raw market data. Never overwrite or silently transform raw source files.
2. Use stable security identity (ISIN/security ID) rather than ticker symbols as permanent identity.
3. Enforce point-in-time (PIT) NIFTY 50 membership.
4. Never use future information in universe, features, signals, execution, or validation.
5. Executable prices must come from raw exchange data plus an explicit corporate-action/accounting layer; do not silently substitute adjusted Yahoo prices.
6. Corporate actions must live in a canonical, auditable ledger. Never hard-code a one-off price adjustment inside the backtest.
7. All normalization, feature selection, parameter selection, and model fitting must occur only on information available to the relevant training/research period.
8. Transaction costs, slippage, taxes, integer shares, cash, and execution timing must be explicit.
9. The final holdout must remain technically isolated until the research specification is frozen.
10. Do not delete failed experiments or unfavorable results.
11. Do not change strategy rules, benchmarks, evaluation periods, or success criteria after seeing results without recording a new experiment.
12. AI-generated code must be tested and reviewed; an AI-generated PASS statement is not evidence by itself.
13. Deterministic data checks must be performed by Python/tests, not by narrative judgment.
14. Every important data transformation needs a reproducible test.
15. Do not begin Phase 1 while phase0_gate.py reports FAIL or UNVERIFIED critical checks.

## Frozen primary strategy (for later phases)

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

Do not change these rules merely because an early result is inconvenient.

## Phase 0 gate

Phase 0 must establish, at minimum:

- authoritative/reconciled NSE trading calendar,
- complete raw price archive for the declared research period,
- manifest/hash integrity,
- schema/date integrity,
- security identity transitions,
- PIT NIFTY 50 membership,
- PIT price coverage,
- corporate-action coverage/reconciliation.

Any critical FAIL or UNVERIFIED blocks Phase 1.
CONDITIONAL requires an explicitly documented scope limitation and approval before proceeding.
PASS requires reproducible evidence.
