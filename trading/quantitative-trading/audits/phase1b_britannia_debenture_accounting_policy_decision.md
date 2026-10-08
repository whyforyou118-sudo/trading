# Britannia Bonus Debentures — Accounting Policy Decision

**Status:** PROPOSED FOR REVIEW — NOT APPROVED  
**Scope:** Phase 1B corporate-action accounting only  
**Performance authorization:** NO  
**Frozen V6:** Must not be changed silently. Any selected policy that changes the registered protocol requires a versioned amendment and a new freeze before Run 1.

## 1. Why this decision is required

The raw-price coverage audit passes, but the price files do not contain observations on either instrument's redemption date. The last observed raw prices are 18 August 2022 for ISIN `INE216A07052` and 21 May 2024 for ISIN `INE216A08027`. A passing coverage audit does not define how the portfolio should value the entitlement before listing or account for coupon and redemption cash flows.

## 2. Verified instrument facts

| Field | 2019 issue | 2021 issue |
|---|---|---|
| ISIN | `INE216A07052` | `INE216A08027` |
| Instrument | 3-year secured, non-convertible, redeemable bonus debenture | 3-year unsecured, non-convertible, redeemable bonus debenture |
| Entitlement | 1 debenture per eligible equity share | 1 debenture per eligible equity share |
| Face value | ₹30 | ₹29 |
| Coupon | 8% p.a., payable annually | 5.5% p.a., payable annually |
| Record date | 23 Aug 2019 | 27 May 2021 |
| Allotment / listing | Allotted 28 Aug 2019; listing effective 9 Oct 2019 | Allotted 3 Jun 2021; listing effective 20 Jul 2021 |
| Redemption | 26 Aug 2022; issuer says principal and interest were repaid | 3 Jun 2024; issuer confirms third-year interest and redemption were paid |

Primary/source references:
- NSE/Britannia issuer notice for the 2019 debenture repayment and interest on 26 Aug 2022: https://nsearchives.nseindia.com/corporate/BRITANNIA_04112022214406_Outcome_Signed.pdf
- Britannia 2023–24 annual report (issue terms, record dates, listing and redemption): https://nsearchives.nseindia.com/annual_reports/AR_24587_BRITANNIA_2023_2024_1907202401243.pdf
- NSE issuer filing for the 2021 issue terms, annual coupon and bullet redemption: https://archives.nseindia.com/corporate/BRITANNIA_03062021131616_OUTCOMEOFBDC03062021.pdf
- Britannia confirmation of 2021 issue third-year interest and redemption payment: https://media.britannia.co.in/Regulation_57_3rd_Year_Interest_and_Redemption_of_Bonus_Debentures_978c760df3.pdf
- NSE corporate-action listing confirms the 2019 and 2021 one-debenture-per-share scheme events: https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=BRITANNIA

## 3. Accounting requirements that are not optional

1. Track the debenture as a **separate debt instrument**, never as additional equity shares.
2. Determine entitlement from eligible parent-equity shares under the scheme's record-date rules; do not use shares bought after the ex-date to create entitlement.
3. Record each contractual coupon once, on the applicable entitlement/payment rule; do not duplicate a coupon or include it in both market price and cash.
4. On redemption, remove the debenture position and credit the confirmed principal plus the applicable final coupon exactly once.
5. Use raw, source-traceable instrument prices when available. Do not carry a stale market price beyond redemption.
6. Reconcile cash, instrument quantities, and NAV before and after each event.
7. Preserve the ₹12.50 Britannia dividend associated with the 2021 scheme as a separate dividend event; it must not be conflated with the debenture.
8. Do not assume face value equals fair value merely because it is the contractual redemption amount.

## 4. Valuation gap and policy choices

The raw equity/debenture bhavcopy files establish prices from the debenture listing dates onward, but do not provide a market price on the earlier entitlement/ex-date. That gap must not be filled using a future listing price without explicitly acknowledging look-ahead.

### Option A — Independent ex-date fair-value source (preferred if obtainable)

Obtain a contemporaneous, independently sourced ex-date fair value for each entitlement. Recognize the entitlement at that value on the effective entitlement date, mark it using raw market prices after listing, book coupons as cash flows, and redeem at the confirmed principal plus final coupon. Record the source, timestamp, and valuation method. If a reliable ex-date value cannot be found, this option is not implementable as written.

### Option B — Pre-registered provisional face-value convention (requires explicit protocol amendment)

Recognize the entitlement at contractual face value on the entitlement date, then mark to observed raw prices from the first tradable date and account for coupons/redemption separately. This is reproducible and uses terms known at the time, but **face value is a valuation assumption, not evidence of fair value**. Report a sensitivity analysis because the convention can affect returns.

### Option C — Delay recognition until listing (not recommended as the primary estimate)

Do not recognize the asset until its first tradable date. This avoids inventing an ex-date price but omits an economically real entitlement during the pre-listing interval and can create a discontinuous NAV jump at listing. Use only as a sensitivity, not as a neutral accounting solution.

**Prohibited shortcut:** using the first listing price to value the asset retroactively on the ex-date without labeling this as look-ahead. Do not treat the debenture as an equity conversion or silently drop the entitlement.

## 5. Recommendation and current decision

Recommendation: first attempt Option A by searching issuer/exchange records for a defensible contemporaneous valuation on the ex-date. If no such source exists, present Option B to the project owner for explicit approval as a **versioned protocol amendment**, with Option C as a sensitivity. No choice is approved by this document.

Until the valuation convention is explicitly approved and versioned, both Britannia rows remain performance blockers. No historical performance run is authorized by this memo.

## 6. Acceptance tests required after policy approval

- Entitlement count equals eligible parent shares under the verified ratio.
- Entitlement date and record-date logic are tested against the corporate-action timeline.
- Coupon amounts and payment dates reconcile to primary issuer notices; each cash flow is booked once.
- Redemption principal and final interest are credited once, and the instrument position is removed on redemption.
- No market mark is used after redemption.
- Daily/quarterly NAV continuity is tested around ex-date, listing, coupon, and redemption dates.
- The result is invariant to input event ordering when events have different dates; same-day priority is explicitly tested.
- A hand-calculated sample ledger independently reproduces cash, position quantities, costs, and NAV.
- Audit artifacts state the selected valuation convention, evidence URLs, source timestamps, code version, and whether the convention amended V6.

**Run 1 gate:** remain blocked until this decision is approved, implemented, tested, reconciled, and included in a clean final freeze.
