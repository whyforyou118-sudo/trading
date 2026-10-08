# Britannia Debenture Cash-Flow Reconciliation Register

**Status:** PARTIAL — NOT CLEARED FOR HISTORICAL PERFORMANCE  
**Policy amendment:** `BRIT-DEB-FACE-VALUE-V1`  
**Branch:** `phase1b-britannia-accounting-v1`  
**Purpose:** Record primary-source-backed event dates and distinguish verified facts from unresolved per-debenture cash amounts. Do not treat this register as an executable event ledger until every required field is reconciled.

## 1. 2019 secured debenture

- ISIN: `INE216A07052`
- Face value: ₹30
- Coupon: 8% p.a.
- Entitlement: one debenture per eligible equity share; ex-date 22 August 2019, record date 23 August 2019.
- Allotment: 28 August 2019.
- First listing/trading date: 9 October 2019.
- First-year interest: issuer annual-report disclosure says paid on 28 August 2020.
- Second-year interest: issuer annual-report disclosure says paid on 30 August 2021 to holders on record date 26 August 2021.
- Third-year interest plus redemption: issuer disclosures say paid on 26 August 2022 to holders on record date 22 August 2022; principal is ₹30 per debenture.
- Contractual terms specify actual days elapsed in a 365/366-day year. Therefore, do not hard-code ₹2.40 for every coupon without reconciling the applicable accrual period and issuer's paid amount.
- Exact per-debenture amount for each payment: **PENDING PRIMARY-SOURCE RECONCILIATION**.
- Primary references:
  - Terms / coupon dates / day-count basis: https://nsearchives.nseindia.com/corporates/offerdocument/scheme/IM_BRITANNIA.pdf
  - 2020 first-year interest disclosure: https://nsearchives.nseindia.com/corporate/BRITANNIA_19102020170628_BILBSENSEOUTCOME.pdf
  - 2021 second-year interest disclosure: https://nsearchives.nseindia.com/corporate/BRITANNIA_03062022000002_IntimationAnnualReport2022.pdf
  - 2022 redemption and final interest: https://nsearchives.nseindia.com/corporate/BRITANNIA_03082023000240_NSEAnnualReportSigned.pdf and https://nsearchives.nseindia.com/corporate/BRITANNIA_04112022214406_Outcome_Signed.pdf

## 2. 2021 unsecured debenture

- ISIN: `INE216A08027`
- Face value: ₹29
- Coupon: 5.5% p.a.
- Entitlement: one debenture per eligible equity share; ex-date 25 May 2021, record date 27 May 2021.
- Allotment / deemed issue date: 3 June 2021.
- First listing/trading date: 20 July 2021.
- First-year interest: issuer annual-report disclosure says paid on 3 June 2022 to holders on record date 27 May 2022.
- Second-year interest: **PAYMENT DATE AND AMOUNT REQUIRE PRIMARY-SOURCE CONFIRMATION**.
- Third-year interest and redemption: due/remitted on 3 June 2024; principal is ₹29 per debenture. The 2024–25 annual report says ₹7,47,549 of third-year interest and ₹1,46,62,690 of redemption amount relating to the issue were remitted to IEPF on 3 June 2024; these are unclaimed aggregate amounts, not the total issue-wide coupon.
- Exact per-debenture amount for each payment: **PENDING PRIMARY-SOURCE RECONCILIATION**.
- Primary references:
  - 2022–23 annual report (first-year interest paid 3 June 2022): https://nsearchives.nseindia.com/corporate/BRITANNIA_03082023000240_NSEAnnualReportSigned.pdf
  - 2023–24 annual report (third-year due date): https://nsearchives.nseindia.com/annual_reports/AR_24587_BRITANNIA_2023_2024_1907202401243.pdf
  - 2024–25 annual-report notice (unclaimed third-year interest/redemption remitted to IEPF): https://nsearchives.nseindia.com/corporate/BRITANNIA1_19072025235052_Intimation_Signed.pdf
  - Issue terms / allotment: https://archives.nseindia.com/corporate/BRITANNIA_03062021131616_OUTCOMEOFBDC03062021.pdf

## 3. Required reconciliation before ledger ingestion

For every payment event, add a source-backed record with:
1. instrument ISIN and unique event ID;
2. payment date and the applicable record/eligibility date, if relevant;
3. exact amount per debenture, supported by the issuer notice or a transparent calculation tied to the governing terms;
4. calculation period, day count and rate where calculated;
5. whether the final coupon is included in the redemption cash flow (it must not be booked twice);
6. source URL, relevant quoted text/page, and reviewer status.

Do not substitute a coupon-rate calculation for a confirmed cash payment when the issuer payment period or day-count convention is unresolved. Do not infer an issue-wide payment from an unclaimed-account/IEPF aggregate. The event ledger must remain blocked until all coupon dates and amounts reconcile.

## 4. Gate

**Current result: BLOCKED.** This register is a research checklist, not approval to run the historical simulation. Keep Performance Run 1 unauthorized until coupon amounts/dates, redemption cash flows, entitlement counts, NAV continuity, and listing-only sensitivity are validated and the final freeze is complete.
