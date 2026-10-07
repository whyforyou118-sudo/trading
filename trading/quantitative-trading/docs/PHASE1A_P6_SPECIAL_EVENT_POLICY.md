# Phase 1A P6 Special Corporate-Action Policy

This policy is part of the frozen V6 implementation audit. It does not change V6
parameters.

## 1. Ordinary dividends

NSE subject variants containing dividend, including common source spelling
variants such as "Dividned", are classified as cash distributions. AGM text
combined with a dividend is still a dividend event. The event must use the
NSE ex-date and the production ledger's dividend convention.

## 2. Equity bonus and split

Only an actual equity bonus or face-value split/subdivision/consolidation is
eligible for a share-ratio action. A scheme that distributes a debenture is
not an equity bonus.

NSE's corporate-action adjustment guidance treats bonus, rights, merger/
demerger, amalgamation, splits and consolidations as stock benefits and
dividend as a cash benefit. The production implementation must preserve the
security identity and event date rather than infer factors from subject text.

## 3. Rights

Rights issues are NOT silently treated as ordinary dividends or bonus shares.
A rights event requires an explicit ex-rights economic treatment before it can
enter the signal-adjustment engine.

For an issue A:B at subscription price S, with cum-date underlying close P,
NSE's corporate-action methodology defines the benefit per right and an
adjustment factor from the rights entitlement and issue price. This formula
may be used as a reference for signal-price adjustment, but the research
implementation must separately specify whether the investor is assumed to
subscribe, renounce, or let the entitlement lapse. The frozen V6 portfolio
must not receive a free synthetic subscription unless explicitly modeled.

## 4. Britannia bonus-debenture scheme

The Britannia scheme records are NOT equity bonus events. The scheme issued
one 5.5% unsecured, non-convertible, redeemable debenture of face value
INR 29 for every one equity share held. The separate INR 12.50 dividend is a
cash distribution.

The debenture is a different security. Face value must not be substituted for
market value in a total-return series. Until an auditable ex-date market-value
and entitlement/reconciliation treatment is implemented, these scheme events
remain a hard P6 blocker.

## 5. Buybacks

Buybacks are not converted into a mechanical price adjustment. They may affect
security economics, but no synthetic adjustment factor is invented from the
NSE subject string.

## 6. Fail-closed rule

Any economically material rights, scheme, merger, demerger, redemption,
capital reduction, security distribution, or unresolved event without a
validated production treatment blocks P6.

No performance run is authorized while such a blocker remains.

## Sources

- NSE Corporate Action adjustment methodology.
- NSE Rights Issue / Rights Entitlement guidance.
- Britannia/NSE scheme filings for the bonus debenture and INR 12.50 dividend.
