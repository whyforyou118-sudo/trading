# Phase 0.5 Zerodha Cost Evidence Research

Status: BLOCKED — historical date-effective cost schedule is not yet complete.

## Scope

The primary research interval is 2018-01-01 through 2025-12-31. The cost model must not apply current Zerodha rates backward through the entire interval.

The cost schedule must contain date-effective rows with source references for:
- equity-delivery brokerage
- STT buy/sell
- NSE equity-delivery transaction charge
- SEBI turnover charge
- stamp duty on buys
- GST/service tax
- Zerodha/DP sale charge

No rate is marked verified unless the historical effective date and source are supported.

## Verified evidence located

### Equity-delivery brokerage

Zerodha states that it has charged zero brokerage for equity-delivery trades since 2015-12-01.

Source: Zerodha Z-Connect, "Brokerage Edge".
Reference: https://zerodha.com/z-connect/trending/brokerage-edge

### STT

Zerodha's historical STT article states that equity-delivery STT was 0.1% on both buy and sell sides from at least 2013 onward. The current Zerodha charges page continues to show 0.1% on both sides.

Sources:
- https://zerodha.com/z-connect/general/new-stt-and-ctt-rates
- https://zerodha.com/charges/

This supports the 0.1% delivery STT assumption for the research interval, subject to final source review.

### GST / service tax transition

Zerodha's GST implementation bulletin states that GST for financial-organization services became 18% from 2017-07-01, replacing the 15% service-tax rate.

Source: Zerodha Market Intelligence, "GST Implementation".
Reference: https://zerodha.com/marketintel/bulletin/386/post

Therefore 2018-01-01 onward can use 18% GST for the applicable taxable service components, subject to final cost-model review.

### Stamp duty

Zerodha states that uniform stamp duty became effective 2020-07-01. Equity-delivery stamp duty is 0.015% on the buy side.

Sources:
- https://zerodha.com/z-connect/general/uniform-stamp-duty
- https://zerodha.com/marketintel/bulletin/259741/

Before 2020-07-01, stamp duty varied by the investor's state of residence. The project therefore must not silently apply 0.015% to the pre-July-2020 period.

### NSE equity-delivery transaction charge

Verified Zerodha historical change points:
- 2018 through 2023-03-31: 0.00345%.
- 2023-04-01 through 2024-03-31: 0.00325%.
- 2024-04-01 through 2024-09-30: 0.00322%.
- 2024-10-01 onward: 0.00297%.

Sources:
- https://zerodha.com/varsity/chapter/clearing-and-settlement-process/
- https://zerodha.com/marketintel/bulletin/347967/revision-in-transaction-charges-and-stt-from-1st-april-2023
- https://zerodha.com/marketintel/bulletin/373933/revision-in-nse-transaction-charges-from-april-1-2024
- https://zerodha.com/marketintel/bulletin/391488/revision-in-transactions-charges-from-1st-october-2024

## Still requiring evidence before verification

### Pre-2020-07-01 stamp duty

This is state-dependent. The project must choose and document a research convention appropriate for an India-wide NIFTY 50 strategy. No universal pre-2020 rate is currently inserted.

### DP charge history

The current Zerodha documentation gives a male-primary-holder charge of Rs.13 plus 18% GST = Rs.15.34 per stock sold, with one DP charge per stock per day. This is current evidence, not historical evidence for 2018-2025.

Source: https://zerodha.com/support/what-do-dp-charges-mean

Historical DP fee changes must be verified before the schedule is marked complete.

### SEBI turnover charge history

The current Zerodha charges page states Rs.10/crore plus GST. A historical effective-date source for the entire 2018-2025 interval still needs to be collected before marking the schedule verified.

## Gate rule

Until every required component has date-effective historical evidence covering 2018-2025, the verified field remains FALSE and Phase 0.5 remains BLOCKED.

Do not fabricate or backfill missing historical rates from the current Zerodha charges page.
