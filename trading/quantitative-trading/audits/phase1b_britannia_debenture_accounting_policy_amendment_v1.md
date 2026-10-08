# Britannia Bonus Debentures — Accounting Policy Amendment V1

**Status:** APPROVED FOR IMPLEMENTATION BY PROJECT OWNER ON 9 October 2026  
**Amendment ID:** `BRIT-DEB-FACE-VALUE-V1`  
**Applies to:** Phase 1B accounting implementation on branch `phase1b-britannia-accounting-v1`  
**Frozen V6 baseline:** `8c5ab68` remains unchanged  
**Performance Run 1:** NOT AUTHORIZED

## 1. Decision and evidence check

The targeted source review found issuer/exchange evidence for contractual terms, entitlement dates, listing dates, coupons and redemption. It did **not** find an independent, contemporaneous fair-value observation for either debenture on its ex-date. The first available market quotes occur after entitlement:

- 2019 debenture: ex-date 22 August 2019; record date 23 August 2019; allotted 28 August 2019; listed 9 October 2019.
- 2021 debenture: ex-date 25 May 2021; record date 27 May 2021; allotted 3 June 2021; listed 20 July 2021.

The 2019 listing-day price reported by contemporaneous market coverage is post-entitlement and MUST NOT be backfilled onto the ex-date. It is not a contemporaneous ex-date fair value. No comparable ex-date trade was identified for the 2021 instrument either.

The project owner has directed implementation of the provisional face-value convention if this final source check found no reliable ex-date fair value. This document records that decision as an explicit, versioned protocol amendment; it does not silently alter the protected V6 baseline.

## 2. Approved provisional valuation convention

1. On the ex-date, recognize one separate debt-instrument unit per eligible Britannia equity share held at the prior close, using the registered 1:1 entitlement ratio and the scheme's fractional-unit rules.
2. For provisional NAV recognition from ex-date until the instrument's first tradable date, mark each debenture at its contractual face value: ₹30 for the 2019 issue and ₹29 for the 2021 issue.
3. From the first tradable date onward, use source-traceable raw, unadjusted debenture prices when available. Do not use the future listing price to revise an earlier date.
4. Coupons are explicit, source-backed cashflow events. The ledger must not infer, duplicate, or derive a payment solely from the coupon rate; the actual amount/date must reconcile to issuer evidence.
5. On redemption, remove every outstanding unit and credit the confirmed principal plus the final coupon exactly once. Do not also post the final coupon as a separate coupon event.
6. If an expected coupon or redemption amount/date cannot be independently reconciled, fail closed and block historical performance evaluation.
7. Keep the 2021 scheme's ₹12.50 equity dividend as a separate dividend event.
8. Run the delayed-recognition convention (recognition only at listing) as a sensitivity. Report the difference in portfolio NAV/returns against this provisional face-value convention.

**Interpretation:** Face value is a deterministic provisional valuation assumption, not evidence that fair value equaled face value. Results must disclose this limitation and the required sensitivity. This amendment is not a claim of accounting-standard fair value.

## 3. Source register

- NSE corporate-actions table, Britannia symbol: https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=BRITANNIA
- 2019 issue allotment (₹30 face value, 1:1 ratio, record date 23 August 2019): https://nsearchives.nseindia.com/corporate/BRITANNIA_28082019165059_OUTCOMEBONUSDEBENTURECOMMITTEEALLOTMENT_260.pdf
- 2019 issue terms, annual coupon schedule and actual/365-or-366 day-count basis: https://nsearchives.nseindia.com/corporates/offerdocument/scheme/IM_BRITANNIA.pdf
- 2019 issuer repayment notice: https://nsearchives.nseindia.com/corporate/BRITANNIA_04112022214406_Outcome_Signed.pdf
- 2021 issue terms, allotment date, 5.5% coupon and redemption date: https://archives.nseindia.com/corporate/BRITANNIA_03062021131616_OUTCOMEOFBDC03062021.pdf
- 2021 listing effective 20 July 2021: https://archives.nseindia.com/corporate/BRITANNIA_19072021194130_IntimationtoSEforBonusDebentures.pdf
- Britannia 2023–24 annual report: https://nsearchives.nseindia.com/annual_reports/AR_24587_BRITANNIA_2023_2024_1907202401243.pdf

These sources support contractual terms and lifecycle dates. They do not supply an independent ex-date fair value. Actual per-payment amounts and payment dates must still be transcribed and reconciled from the issuer's payment notices before a historical run.

## 4. Implementation contract

The accounting ledger must support three distinct event types:

- **Entitlement:** event ID, ex-date, parent symbol, debt-instrument symbol, entitlement ratio, face value, coupon rate, and source reference. Entitlement is based on the parent position before same-day open trades.
- **Coupon:** unique event ID, payment date, debt symbol, amount per outstanding unit, and source reference.
- **Redemption:** unique event ID, redemption date, debt symbol, principal per unit, final coupon per unit, and source reference. The position is removed after crediting the combined cashflow.

Event IDs are required to fail closed on duplicate debenture cashflows. A debt instrument must be held under its own symbol and must never be merged into the equity position.

## 5. Acceptance gates — all required before Run 1

- [ ] Entitlement count matches eligible prior-close equity shares for both ex-dates.
- [ ] Same-day open purchases do not create entitlement; same-day sales do not erase entitlement already determined from the prior close.
- [ ] The provisional face-value mark is applied only before first tradable pricing; raw prices are used thereafter.
- [ ] Every annual coupon is reconciled to primary issuer evidence and booked once.
- [ ] Redemption principal and final coupon reconcile to issuer notices, are credited once, and remove the debt position.
- [ ] No post-redemption market mark is requested or applied.
- [ ] The ₹12.50 2021 dividend remains separate from the debenture entitlement.
- [ ] Daily NAV/cash/positions are hand-reconciled around ex-date, listing, coupon and redemption.
- [ ] Listing-only sensitivity is produced and reported.
- [ ] Full regression suite and the corporate-action preflight pass.
- [ ] Final manifest identifies this amendment, its commit, sources, data hashes and valuation convention.

**Gate:** This amendment authorizes implementation and testing only. It does not authorize historical performance Run 1. Run 1 remains blocked until every acceptance gate above and all other Phase 1A/1B preflight gates pass and a clean final freeze is created.
