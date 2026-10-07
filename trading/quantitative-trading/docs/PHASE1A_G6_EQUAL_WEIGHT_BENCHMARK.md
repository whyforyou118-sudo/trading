# Phase 1A G6 — Nifty50 Equal Weight Benchmark

## Benchmark definition

The secondary benchmark is the **official NSE Indices Nifty50 Equal Weight Total Return Index**, not a project-reconstructed equal-weight portfolio.

NSE Indices states that Nifty50 Equal Weight contains the same companies as Nifty 50 and assigns equal weights. Its methodology specifies semi-annual composition changes with Nifty 50 and additional quarterly weight alignment; the total-return version includes constituent dividends reinvested after the ex-date.

Official references:

- https://www.niftyindices.com/indices/equity/strategy-indices/nifty50-equal-weight
- https://www.niftyindices.com/methodology/nifty50_equal_weight_methodology.pdf
- https://www.niftyindices.com/reports/historical-data

## Reproducibility rule

The project must use the official historical TR series returned by NSE Indices. It must not reconstruct the benchmark from local stock prices, because doing so could silently diverge from official divisor, corporate-action, rebalancing, and dividend conventions.

Downloader:

`src/data/download_nifty50_equal_weight_tri.py`

Expected artifact:

`data/reference/nifty50_equal_weight_tri.csv`

Expected schema:

`date,value,source,source_reference`

Research interval:

2018-01-01 through 2025-12-31.

## Gate rule

G6 remains BLOCKED until the artifact exists and contains a date-complete, unique, positive-value historical series for the frozen research interval. The benchmark is secondary and does not alter the frozen trading strategy.
