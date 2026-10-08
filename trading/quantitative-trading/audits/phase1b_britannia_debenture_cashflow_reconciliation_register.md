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
- Second-year interest: CDSL records record date 17 May 2023, due/actual payment date 3 June 2023, and aggregate interest paid ₹38.42 crore. This confirms the event date, but the aggregate is rounded and is not exact per-debenture evidence.
- Third-year interest: the issuer's 3 June 2024 notice records record date 22 May 2024, due/actual payment date 3 June 2024, and interest of ₹38.42 crore; the issuer confirms principal redemption on the same date. The amount is rounded at issue level, not exact per-debenture evidence.
- **Day-count source conflict:** CDSL's database labels the convention Actual/365, while the issue information memorandum says Actual/Actual and specifies actual days in a 365/366-day year. Do not select one silently. Resolve this against the executed debenture trust deed / definitive issue terms and reconcile the issuer's payment calculations before setting coupon amounts.
- Third-year interest and redemption: due/remitted on 3 June 2024; principal is ₹29 per debenture. The 2024–25 annual report says ₹7,47,549 of third-year interest and ₹1,46,62,690 of redemption amount relating to the issue were remitted to IEPF on 3 June 2024; these are unclaimed aggregate amounts, not the total issue-wide coupon.
- Exact per-debenture coupon amount for each payment: **PENDING PRIMARY-SOURCE RECONCILIATION**. The rounded aggregate is consistent with a nominal ₹1.595 per debenture but is not enough to establish the actual amount or settle the day-count convention.
- Primary references:
  - CDSL corporate-bond database, including payment status for 3 June 2023 and its stated Actual/365 convention: https://www.cdslindia.com/CorporateBond/CorpBondDatabase.aspx?ISIN=INE216A08027
  - Issuer's 3 June 2024 payment confirmation, including 22 May 2024 record date: https://media.britannia.co.in/Regulation_57_3rd_Year_Interest_and_Redemption_of_Bonus_Debentures_978c760df3.pdf
  - Issue information memorandum stating Actual/Actual basis: https://www.bseindia.com/downloads/ipo/2021714135249IM%20Britannia.pdf
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


## 5. Additional primary-source search pass (9 October 2026)

This pass found additional issuer/exchange-hosted disclosures, but **did not locate an executed debenture trust deed or an issuer payment advice that states exact per-debenture coupon cash for every payment**. The accounting gate therefore remains blocked.

### 2019 issue — additional evidence

- Britannia's audited-results filing dated 2 June 2020 confirms 240,318,294 debentures of ₹30 each, coupon 8% p.a., annual interest, and first interest due on 28 August 2020: https://nsearchives.nseindia.com/corporate/BRITANNIA_02062020171301_BRITANNIA.pdf
- Britannia's Q2 FY2021–22 results filing says second-year interest was paid on 30 August 2021 because 28 August 2021 was a bank holiday; it states the third-year interest plus ₹30 principal was due on 28 August 2022: https://nsearchives.nseindia.com/corporate/BILFinancialResults30092021signed_08112021153437.pdf
- Britannia's 2022–23 annual report says the 2019 issue was redeemed on 26 August 2022 and third-year interest plus redemption was paid to holders on the 22 August 2022 record date: https://nsearchives.nseindia.com/corporate/BRITANNIA_03082023000240_NSEAnnualReportSigned.pdf
- These records corroborate issue size and payment chronology, but do not provide the exact coupon paid per debenture. The offering memorandum's actual-days-in-a-365/366-day-year wording remains the relevant disclosed basis; the governing calculation and exact cash paid still require reconciliation.

### 2021 issue — additional evidence

- The issuer's 3 June 2021 outcome filing confirms 5.5% p.a., annual coupon payments after each 12-calendar-month period from allotment, allotment date 3 June 2021 and redemption date 3 June 2024: https://archives.nseindia.com/corporate/BRITANNIA_03062021131616_OUTCOMEOFBDC03062021.pdf
- Britannia's 2022–23 annual report confirms first-year interest was paid on 3 June 2022 to record-date holders as of 27 May 2022: https://nsearchives.nseindia.com/corporate/BRITANNIA_03082023000240_NSEAnnualReportSigned.pdf
- These records corroborate the contractual schedule but do not resolve the CDSL Actual/365 versus information-memorandum Actual/Actual conflict or establish exact per-debenture cash for all three coupon events.

### Evidence still required

1. Executed debenture trust deed or definitive instrument terms for each ISIN, including the operative day-count clause and business-day adjustment.
2. Issuer/registrar/debenture-trustee payment advice or another primary record giving the exact per-debenture coupon for each event, or a reproducible calculation explicitly reconciled to the issuer's actual paid amount.
3. Confirmation of whether the final coupon is a separate cash payment or included in the redemption amount for each instrument.

**No coupon values were inferred or entered in this pass.** Do not use nominal rate × face value as a substitute for the verified cash flow, and do not use rounded issue-wide totals to reverse-engineer exact per-unit payments.


## 6. Follow-up findings: exact unclaimed-interest aggregates and trustee trail (9 October 2026)

### 2021 issue — distinguish unclaimed interest from total coupon paid

Britannia's official 2023–24 annual report identifies two separate amounts relating to the ₹29 debenture issue that were remitted to IEPF:
- **Second-year interest:** ₹7,47,744.35 remitted on 3 June 2023.
- **Third-year interest:** ₹7,47,548.98 remitted on 3 June 2024.

Source: https://nsearchives.nseindia.com/annual_reports/AR_24587_BRITANNIA_2023_2024_1907202401243.pdf (IEPF-related information section, printed page 11).

These are exact unclaimed-interest aggregates, not the issue-wide coupon payments and not exact per-debenture coupon evidence. Keep them separate from the rounded ₹38.42 crore issue-level interest amounts. They must not be used to infer coupon cash paid to all holders.

### Trustee and registrar route

Britannia's 2020–21 annual report identifies IDBI Trusteeship Services Limited as trustee and KFin Technologies Private Limited as registrar for the 2019 ₹30 issue:
https://media.britannia.co.in/Annual_Report_2020_21_be3a70d511.pdf

Britannia's 2023–24 annual report identifies IDBI Trusteeship Services Limited as trustee and KFin Technologies Limited as registrar for the ₹29 issue:
https://nsearchives.nseindia.com/annual_reports/AR_24587_BRITANNIA_2023_2024_1907202401243.pdf

These are practical primary-source contacts for requesting the executed trust deed / definitive terms, coupon computation basis, payment advice, and exact per-debenture cash paid for each coupon event. No trust deed or complete per-unit payment advice was found in this search pass.

### Gate remains unchanged

No exact per-debenture coupon values have been approved for event-ledger ingestion in this pass. The 2021 Actual/365 versus Actual/Actual conflict remains unresolved. Continue to block historical performance until definitive terms and payment calculations reconcile, including whether the final coupon is separately paid or bundled with redemption.


## 7. Quantitative coupon cross-check against the issuer's rounded aggregate (9 October 2026)

A useful arithmetic cross-check is now available for the 2021 ₹29 issue (24,08,68,296 debentures; coupon 5.5%; annual dates 3 June 2022, 2023 and 2024).

- Nominal annual coupon per debenture: ₹29 × 5.5% = ₹1.595.
- For the 3 June 2023 to 3 June 2024 coupon period, the calendar interval includes 29 February 2024 and has 366 elapsed days.
- Applying the information memorandum's stated Actual/Actual method for a 366-day year gives ₹1.595 per debenture and ₹38,41,84,932.12 across 24,08,68,296 debentures, which rounds to ₹38.42 crore.
- Applying a simple Actual/365 multiplier to that 366-day interval instead gives approximately ₹38.52375 crore, which rounds to ₹38.52 crore—not the issuer's reported ₹38.42 crore aggregate.

Sources for inputs: issue quantity, face value, rate and Actual/365 database metadata in CDSL's record https://www.cdslindia.com/CorporateBond/CorpBondDatabase.aspx?ISIN=INE216A08027; annual coupon dates and Actual/Actual terms in the issuer's information memorandum https://www.bseindia.com/downloads/ipo/2021714135249IM%20Britannia.pdf; 3 June 2024 rounded aggregate in the issuer's payment notice https://media.britannia.co.in/Regulation_57_3rd_Year_Interest_and_Redemption_of_Bonus_Debentures_978c760df3.pdf.

**Interpretation:** The 2024 aggregate is quantitatively consistent with the disclosed Actual/Actual terms and inconsistent with applying Actual/365 to the 366-day interval. This is strong corroborative evidence that the CDSL Actual/365 field may be generic or erroneous for this issue. It is not, by itself, a substitute for the executed trust deed or an exact payment advice; retain the formal-term confirmation requirement and do not silently overwrite the source conflict.

This cross-check is for the 2021 issue only. It does not establish exact per-debenture amounts for the 2019 issue's coupons.
