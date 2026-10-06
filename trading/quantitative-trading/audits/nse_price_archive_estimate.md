# Estimate of NSE price archive size and download plan

## Trading day count
- Date range: 2017-01-01 to 2025-12-31
- Approx. 252 trading days per year (weekday days minus NSE holidays).
- Total expected trading days: **~2,268** (9 years × 252).

## File size assumptions
- Typical compressed bhavcopy (`.csv.zip`) size: **200 KB – 350 KB**.
- Average we take **275 KB**.
- Expected total compressed download size: **≈ 2,268 × 0.275 MB ≈ 623 MB**.
- Extracted CSV size roughly 1 MB per file.
- Expected total extracted size: **≈ 2.3 GB**.

## Disk requirement
- Keep both compressed and extracted versions ⇒ **~3 GB** of free space needed under `data/raw/prices/`.

## Download time estimate
- Assuming average download throughput of **5 MB/s** (typical broadband):
  - 623 MB / 5 MB·s⁻¹ ≈ **125 seconds** (≈ 2 minutes) for compressed files.
  - Extraction time is negligible compared to download.
- With rate‑limiting (e.g., 1 request per second to be polite) the wall‑clock time will be dominated by the pause:
  - 2,268 seconds ≈ **38 minutes**.

## Conclusion before full download
- The URL pattern works for both legacy and UDiFF formats.
- The sample test on **January 1st** each year returned HTTP 503, which is expected because Jan 1 is a **holiday/weekend** and the archive returns a 503 for non‑trading days.
- To avoid false‑negatives we will target the **first trading day** of each month (or simply use the NSE calendar to generate exact trading dates).

**Next steps**:
1. Generate the full list of trading dates using the NSE calendar (`pandas_market_calendars`).
2. Build the robust downloader (`src/data/download_nse_prices.py`).
3. Execute the downloader, populating `data/raw/prices/download_manifest.csv`.
4. Re‑run the full price‑coverage audit (now with corrected unique‑security handling).
5. Perform the daily PIT‑price coverage audit.

*All estimates are conservative; actual file sizes may vary slightly.*
