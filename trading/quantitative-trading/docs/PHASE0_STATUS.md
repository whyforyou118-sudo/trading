# Phase 0 Status

**Current status: NOT PASSED**

The repository contains partial data-acquisition and audit tooling. Do not begin strategy backtesting until the Phase 0 data foundation is independently verified.

## Known blockers

1. NSE calendar has partial/unverified historical holiday coverage.
2. Downloader currently derives dates from pandas_market_calendars instead of a verified NSE reference calendar.
3. YESBANK and HDFC Ltd → HDFC Bank identity transitions require authoritative reconciliation.
4. Corporate-action coverage requires reconciliation beyond a single API response.
5. Full raw-archive integrity requires filesystem, manifest, hash, ZIP, CSV, and date checks.
6. PIT membership and PIT-price coverage require independent verification.

## Rule

A successful script run is not evidence of a PASS. Phase 0 is complete only when the deterministic gate and required evidence checks pass.