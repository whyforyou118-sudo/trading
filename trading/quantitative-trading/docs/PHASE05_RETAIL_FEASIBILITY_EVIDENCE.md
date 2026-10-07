# Phase 0.5 Retail Feasibility Evidence

## Exact whole-share feasibility results

The frozen Phase 0.5 feasibility run produced 31 executable quarterly decision dates. The final 2025-12-31 decision is blocked because no next trading-day execution exists inside the declared 2018-2025 dataset.

| Starting capital | Rebalances with unbuyable Top-5 | Mean cash | Mean absolute weight deviation |
|---:|---:|---:|---:|
| ₹20,000 | 21/31 | 26.43% | 5.29% |
| ₹25,000 | 19/31 | 24.91% | 4.98% |
| ₹50,000 | 7/31 | 13.05% | 2.61% |
| ₹100,000 | 0/31 | 5.34% | 1.07% |
| ₹500,000 | 0/31 | 1.17% | 0.23% |
| ₹1,000,000 | 0/31 | 0.55% | 0.11% |

These are feasibility diagnostics, not performance results.

## Conservative transaction-cost feasibility

At 0.10% slippage and the verified date-effective Zerodha schedule, the conservative 100%-liquidate-and-rebuild-each-quarter model produced:

| Starting capital | Worst modeled cost drag |
|---:|---:|
| ₹20,000 | 3.29% |
| ₹25,000 | 2.97% |
| ₹50,000 | 2.33% |
| ₹100,000 | 2.01% |
| ₹500,000 | 1.76% |
| ₹1,000,000 | 1.73% |

This is a deliberately conservative upper-bound-style feasibility scenario. It must not be described as realized strategy turnover. Phase 1A/1B will calculate realized transaction-level turnover and cost drag.

## Interpretation

The ₹25,000 primary capital remains frozen. The evidence shows material whole-share/cash friction at that capital level; it does not justify silently increasing the primary capital to ₹100,000.

The implementation is therefore defined as an equal-target Top-5 portfolio with whole-share execution and residual cash, rather than a claim of exactly equal realized weights.
