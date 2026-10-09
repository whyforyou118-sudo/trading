# Britannia Corporate-Action Signal Adjustment Policy V1

**Policy ID:** `BRIT-SIGNAL-ADJ-V1`  
**Scope:** Phase 1B signal-only implementation and sensitivity analysis  
**Frozen V6 baseline:** unchanged  
**Historical Run 1:** NOT AUTHORIZED

## Purpose

The existing momentum implementation uses raw closing prices for the signal return. Britannia distributed separate debenture instruments on 22 August 2019 and 25 May 2021. These dates lie inside quarterly momentum formation windows. No Britannia position was held on either entitlement date, but the event can still distort Britannia's momentum rank. The signal layer must account for the distribution without changing raw execution prices.

## Primary provisional policy

For each event that has occurred by the signal formation end date:

1. Obtain Britannia's raw equity close on the ex-date from the NSE raw-price manifest.
2. Use the versioned provisional distribution value: ₹30 per eligible parent share for the 2019 debenture and ₹29 for the 2021 debenture.
3. Compute the pre-event price factor:

   `factor = parent_equity_raw_close_on_ex_date / (parent_equity_raw_close_on_ex_date + distribution_value)`

4. Multiply only Britannia equity signal prices dated strictly before the ex-date by that factor.
5. Do not adjust a signal formed before the ex-date; future events must not leak into earlier decisions.
6. Do not alter execution-open data or any other symbol's prices.

The factor expresses a provisional total-value-consistent adjustment for a distribution. It is not a claim that the debenture's fair value equals face value. This primary convention follows the existing provisional face-value implementation policy and remains an assumption to disclose.

## Listing-only sensitivity

The sensitivity uses the raw closing price for the exact debenture ISIN on its first tradable date:

- 2019 issue: ISIN `INE216A07052`, first tradable date 2019-10-09.
- 2021 issue: ISIN `INE216A08027`, first tradable date 2021-07-20.

Before that date, the sensitivity makes no adjustment for that event because the listing quote is not yet observable. On or after the first tradable date, it uses the observed raw listing close as the event-value proxy and applies the same factor form. It must fail closed if the exact ISIN/date does not produce one unique raw close. The listing quote is a sensitivity proxy, not a verified ex-date fair value; market movement and accrued-interest differences may exist between ex-date and listing date.

## Outputs

The audit script is `src/audit/phase1b_britannia_signal_adjustment_audit.py`. It creates separate artifacts and does not overwrite the existing frozen/raw selection audit:

- `audits/phase1b_britannia_signal_adjustment_comparison.csv`
- `audits/phase1b_britannia_signal_adjustment_summary.csv`
- `audits/phase1b_britannia_signal_adjustment_events.csv`
- `audits/phase1b_britannia_signal_adjustment_summary.json`

The report compares raw Top-5 selections, primary provisional-face-value selections, and listing-only sensitivity selections for all frozen decision dates. It also checks whether recomputed raw selections match the existing selection artifact.

## Verification and gate rules

Run the focused tests first, then run the signal-adjustment audit. A missing raw parent ex-date close, missing/ambiguous listing quote, or mismatch with the existing raw selection artifact must not be silently patched. Inspect and resolve the specific failure.

A successful signal audit does not verify debenture fair value, complete all generic accounting work, satisfy every Phase 1B gate, or authorize performance Run 1. The existing path-relevance audit remains blocked until the new signal evidence is reviewed and the gate is explicitly updated. The frozen V6 baseline and its artifacts must not be rewritten.
