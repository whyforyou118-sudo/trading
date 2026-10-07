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


## Additional historical evidence verified

### SEBI turnover fee

The historical statutory rate is 0.0001% of turnover, i.e. Rs.10 per crore, for sale and purchase transactions in securities other than debt securities. A 2009 notice reproducing the SEBI amendment shows this rate effective from July 1, 2009. A 2019 amendment continued the cash-segment rate at 0.00010% (Rs.10 per crore).

Sources:
- CSE notice reproducing the 2009 SEBI notification: https://www.cse-india.com/upload/CSE%20Notices%20%26%20Circulars/2009/Notice010709.htm
- CSE notice reproducing the March 22, 2019 SEBI amendment: https://www.cse-india.com/upload/cse_notice/REVISED_SEBI_TURNOVER_FEES.htm
- NSE current statutory reference: https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies

Research implication: Rs.10/crore can be treated as the SEBI turnover-fee rate throughout 2018-2025 for this equity-delivery model, with GST handled separately according to the GST effective period.

### Zerodha DP charge history

Zerodha's own Trading Q&A records establish a Rs.13.5 per-scrip-per-day debit charge as early as March 2016, comprising Rs.8 Zerodha + Rs.5.5 CDSL, with taxes additional. The same Rs.13.5 base charge is documented in November 2018 and remained documented in 2020/2021.

Sources:
- Zerodha Trading Q&A, March 2016: https://tradingqna.com/t/dp-charges-and-stt-charges/5637
- Zerodha Trading Q&A, November 2018: https://tradingqna.com/t/how-to-dp-borkage-charges-calculate-in-zerodha/50236

CDSL's June 2024 operating instructions state that its debit-transaction tariff changed effective June 1, 2024. Zerodha's public discussion records the corresponding Zerodha DP charge reduction from Rs.13.5 to Rs.13 effective June 1, 2024.

Sources:
- CDSL DP Operating Instructions, June 2024: https://www.cdslindia.com/downloads/DP/currentDPs/DP-Operating-Instructions-Chapters-as-on-June-30-2024.pdf
- Zerodha Trading Q&A discussion of the June 1, 2024 reduction: https://tradingqna.com/t/cdsl-reduced-charges-will-zerodha-too/165314

Therefore the working historical DP schedule can be represented as:
- 2018-01-01 through 2024-05-31: Rs.13.50 per scrip sold per day, before GST.
- 2024-06-01 through 2025-12-31: Rs.13.00 per scrip sold per day, before GST.

The project should still preserve the source references and not infer any earlier/later rate outside these evidenced periods.

## Stamp-duty decision still required

The remaining material gap is pre-July-2020 stamp duty.

Zerodha explicitly states that before July 1, 2020 stamp duty varied by the client's state of residence, and notes that Telangana and some other states had maximum caps per contract note. Therefore a single pan-India pre-July-2020 rate would be an unsupported simplification.

Sources:
- Zerodha Uniform Stamp Duty: https://zerodha.com/z-connect/general/uniform-stamp-duty
- NSE Stamp Duty reference: https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes

For the primary cost model, the project must explicitly choose one of these defensible conventions before the schedule can be marked verified:
1. A declared investor-residency state and its historical rate/cap.
2. A documented pan-India convention used only as a sensitivity/upper-bound assumption.
3. A state-agnostic implementation-cost analysis that reports the pre-July-2020 stamp-duty component as a range rather than a single point estimate.

No choice is being silently made here.
