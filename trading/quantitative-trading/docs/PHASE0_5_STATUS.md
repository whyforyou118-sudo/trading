# Phase 0.5 — Research Feasibility Gate

Phase 0.5 is a pre-backtest feasibility layer. It tests whether the frozen research design is capable of being evaluated without first looking at strategy profitability. It does not produce P&L or alpha results.

## Tests

1. Statistical feasibility: actual quarterly decision count, approximate MDES Sharpe, and volatility-scaled annualized excess-return MDE.
2. Whole-share capital feasibility: Top-5 historical selection/price artifact; calculate affordability, residual cash, unbuyable selections and target-vs-actual weight deviation.
3. Cost feasibility: date-effective verified Zerodha delivery schedule plus a conservative full-liquidation/full-rebuild quarterly scenario.
4. NIFTY 50 TRI: daily series plus source metadata and independent verification artifact.
5. PIT: at least five effective dates externally reconciled against official evidence.
6. Corporate actions: at least 20 material events sampled and independently reconciled.

## Run order

    python src/audit/phase05_statistical_feasibility.py
    python src/audit/phase05_capital_feasibility.py
    python src/audit/phase05_cost_feasibility.py
    python src/audit/phase05_evidence_gate.py

The gate is fail-closed.

Evidence complete means required artifacts exist and pass structural checks. It does not mean the strategy has alpha or that the design is statistically powerful for every effect size.

The primary strategy remains PIT NIFTY 50 / 12M / 1M skip / Top-5 / quarterly / long-only / ₹25,000. Broader universes, different holdings and semiannual rebalance remain separate experiments.

## Required artifacts before Phase 1A

- audits/phase05_statistical_feasibility.csv
- audits/phase05_capital_feasibility.csv
- audits/phase05_cost_feasibility.csv
- data/reference/nifty50_tri.csv
- audits/phase05_tri_verification.csv
- audits/phase05_pit_external_reconciliation.csv
- audits/phase05_corporate_action_reconciliation.csv
- verified date-effective Zerodha cost schedule

## Interpretation

If feasibility is acceptable, proceed to Phase 1A — Corporate Actions & PIT Executable Prices.

If feasibility exposes a material design problem, do not patch the backtest to rescue it. Create a new preregistered design version, document the reason for the change, and rerun the relevant feasibility tests before performance evaluation.
