# V6 Real-Money Quantitative Trading — Final Master Blueprint

This document is the repository-level source-of-truth summary for V6.
The machine-readable contract is `config/phase1a_preregistration.json`.

## Frozen primary strategy

- PIT NIFTY 50
- 12-month momentum formation
- 1-month skip
- Top 5
- Quarterly rebalance
- Long-only
- No leverage
- ₹25,000 primary capital
- Equal 20% target per selected name
- Whole shares
- Next actual trading-day open
- RAW_UNADJUSTED executable prices
- 0.10% primary slippage
- ZERODHA_DATE_EFFECTIVE costs
- NO_REPLACEMENT_RETAIN_CASH
- Primary cash return 0%
- Research period 2018-01-01 through 2025-12-31
- Development period 2018-01-01 through 2022-12-31
- 2023-01-01 through 2025-12-31 is descriptive holdout only
- Random-5: 100,000 draws, seed 20261007
- Random-5 one-sided p-value cutoff: <0.10
- Estimand A threshold: >=0.25% mean net excess per quarter
- Estimand B threshold: >=1.00% annualized net excess
- Live personal capital-risk limit: ₹5,000 cumulative loss on ₹25,000

## Economic estimands

### A — signal-level

Fractional/notional capital. Percentage/notional costs and slippage apply. Fixed rupee charges inherently tied to whole-share transactions are excluded and reported separately. Dividends and corporate actions remain explicit.

### B — retail implementation

Exact ₹25,000 whole-share implementation with residual cash, actual transaction costs, slippage, dividends and corporate actions.

A cannot rescue or redefine B.

## Decision rule

### PASS

- Estimand B annualized net excess >=1%;
- Random-5 one-sided p <0.10;
- no material data/accounting/corporate-action defect;
- realistic costs/slippage included.

### FAIL

- Estimand B annualized net excess <=0%; or
- a material validity defect invalidates the result.

### INCONCLUSIVE

Everything else.

INCONCLUSIVE means insufficient evidence, not proof of no edge and not proof of future profitability.

## Hard P5 rules

Before performance:

- retained Top-5 names are resized directly toward computed 20% target shares;
- target NAV is pre-trade portfolio NAV at the next execution open using raw opens;
- ties: momentum descending, then symbol ascending;
- NaN signal: exclude from ranking;
- missing signal price: exclude and record;
- missing execution open: fail closed;
- rights issue: fail closed unless represented in the canonical ledger;
- cash-in-lieu: credit only with authoritative entitlement and amount, otherwise fail closed;
- fewer than five eligible names: hold all eligible names and retain unallocated target capital as cash;
- unsupported corporate action: fail closed;
- dividend convention: ex/entitlement date with authoritative record/payment reconciliation.

P5 is a hard gate.

## P1–P9

1. Human spot-check on three frozen dates.
2. Truncation invariance.
3. Same production-code security conversion path.
4. Reconcile all 42 research-period membership transitions.
5. Lock all operational rules above.
6. Path-conditional corporate-action census; fail closed.
7. Historical cost/benchmark audit.
8. Real dividend replay/invariant.
9. Explicit executable-open source declaration.

Performance is blocked until all nine pass.

## Repository facts

The membership file contains 55 transition rows total and exactly 42 transitions inside the frozen 2018–2025 research period. The 16 announcement/review events are a different count.

The independent reproduction covers 31 quarterly decision dates × 5 selections = 155 selection rows and must be verified from the repository.

## Freeze and Run 1

The existing commit `56d99fb...` remains historical evidence.

After P1–P9 pass:

1. create the final V6 re-freeze commit;
2. record the final configuration SHA256;
3. set `performance_run_allowed=true`;
4. execute Run 1 exactly once;
5. preserve Run 1 permanently;
6. any later execution is Run 2 or later;
7. do not modify V6 after seeing Run 1.

## Forward validation

If justified:

Backtest → exact V6 paper trading → live/backtest parity → exact ₹25K live deployment.

The ₹5,000 live loss limit is a separate capital-preservation rule, not an alpha rule.

## V7

Any material strategy change is V7 or later. V7 is a new experiment and cannot be described as confirmation of V6. Multiple testing must be considered across the research sequence.

## Governing principle

> We are not trying to prove that V6 works. We are trying to determine whether V6 contains a genuine, implementation-surviving edge strong enough to justify risking our own money.

Correctness first. Evidence second. Money last.
