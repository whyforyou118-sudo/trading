# R0 — Repository Verification Report

- Phase: R0
- Blueprint sections enforced: V6 Final Master Blueprint / R0 repository verification; absolute rules 1–9; hard-stop rules.
- Repository: `whyforyou118-sudo/trading`
- Scope: read-only verification of the repository state and frozen artifacts. No performance backtest, strategy returns, Sharpe, CAGR, Random-5 p-values, or benchmark-relative performance were executed.

## What was done

Repository inspected at branch `phase1a-final-preflight`.

HEAD:
- Branch: `phase1a-final-preflight`
- HEAD: `638fb39d236aa0923df916cc0e50d66eaee89a1b`
- HEAD commit: `fix: use live NSE historical index selectors for TRI form`
- Commit date: 2026-10-08 09:32:20 UTC
- Working-tree clean/dirty status: UNVERIFIED. GitHub exposes the committed tree but not a local uncommitted working tree. A local clone attempt failed because this execution environment could not resolve github.com.

A dedicated `preflight/R0` branch was created from the verified HEAD. No source/config/test file was changed.

## Evidence and exact commands

1. Repository metadata:
```
GET https://api.github.com/repos/whyforyou118-sudo/trading
```
Raw relevant output:
```
"default_branch":"main"
"permissions":{"admin":true,"maintain":true,"push":true,"triage":true,"pull":true}
"pushed_at":"2026-10-08T09:32:21Z"
```

2. R0 branch HEAD:
```
GET https://api.github.com/repos/whyforyou118-sudo/trading/git/ref/heads/phase1a-final-preflight
```
Raw output:
```
{"ref":"refs/heads/phase1a-final-preflight",
 "object":{"sha":"638fb39d236aa0923df916cc0e50d66eaee89a1b","type":"commit"}}
```

3. Historical commit verification:
```
GET https://api.github.com/repos/whyforyou118-sudo/trading/commits/56d99fb55021e9935113af390e2216e89c57ffa0
```
Raw result:
```
422 Not Found: No commit found for SHA: 56d99fb55021e9935113af390e2216e89c57ffa0
```
A repository commit-history scan of the current branch's 100 most recent commits also returned:
```
contains_full=false
contains_prefix=false
commit_count=100
```
Global GitHub commit search for `56d99fb` did not return this repository/commit.

4. Frozen config:
```
GET trading/quantitative-trading/config/phase1a_preregistration.json
```
Repository blob SHA:
```
89d9a8dd2fb4fc69725a4abb97a4ce401c82dc29
```
SHA-256 recomputed from the exact UTF-8 file content:
```
9d7f1254bab1e492634c3093e22a916db45d5666c687f19ef277684c1c812a4f
```
Blueprint claim:
```
0059f964d2e5fa5f35e758210c61426f861bead352325db9297b7c281592646d
```
MATCH: FALSE.

The repository freeze manifest additionally records a different historical config blob SHA:
```
a7aeb0763e5d090e99431e12937c487ecb41cebd
```
while the current branch contains blob SHA `89d9a8dd2fb4fc69725a4abb97a4ce401c82dc29`. This is another reproducibility discrepancy.

5. Frozen-parameter comparison:
The current `frozen_primary` values match the Blueprint for the strategy parameters that are explicitly frozen:

| Parameter | Blueprint | Repository | Result |
|---|---|---|---|
| Universe | PIT NIFTY 50 | NIFTY_50_PIT | MATCH |
| Formation | 12 months | 12 | MATCH |
| Skip | 1 month | 1 | MATCH |
| Holdings | Top 5 | 5 | MATCH |
| Rebalance | Quarterly | quarterly | MATCH |
| Capital | Rs 25,000 | 25000 | MATCH |
| Execution | Next actual trading-day open | next_actual_trading_day_open | MATCH |
| Price mode | RAW_UNADJUSTED | RAW_UNADJUSTED | MATCH |
| Slippage | 0.10% | 0.1 | MATCH |
| Cost model | ZERODHA_DATE_EFFECTIVE | ZERODHA_DATE_EFFECTIVE | MATCH |
| Target weight | 20% | 20 | MATCH |
| Direction | Long-only | long_only | MATCH |
| Leverage | None | none | MATCH |
| Cash return | 0% | 0 | MATCH |
| Unbuyable policy | NO_REPLACEMENT_RETAIN_CASH | NO_REPLACEMENT_RETAIN_CASH | MATCH |
| Loss limit | Rs 5,000 | 5000 | MATCH |
| Research period | 2018-01-01 to 2025-12-31 | same | MATCH |
| Development end | 2022-12-31 | same | MATCH |
| Descriptive holdout | 2023-01-01 to 2025-12-31 | same | MATCH |
| Random-5 draws | 100,000 | 100000 | MATCH |
| Random-5 seed | 20261007 | 20261007 | MATCH |
| Random-5 p cutoff | <0.10 | 0.1 | MATCH |
| Estimand A hurdle | >=0.25%/quarter | 0.0025 | MATCH |
| Estimand B hurdle | >=1% annualized | 0.01 | MATCH |

No parameter was changed to resolve the discrepancy.

6. Membership and official review counts:
```
GET trading/quantitative-trading/data/reference/nifty50_membership.csv
GET trading/quantitative-trading/audits/phase1a_gate1_announcement_effective.csv
```
Raw recomputation:
```
membership_rows_total=55
membership_rows_2018-01-01_through_2025-12-31=42
official_review_rows=16
```
These counts MATCH the Blueprint repository-fact claims.

7. G4 independent implementation:
The repository contains `src/audit/phase1a_gate4_independent_reproduction.py`.
Static import inspection shows only Python standard-library imports:
- csv
- datetime
- io
- json
- zipfile
- pathlib

The implementation does not import the primary signal/ranking/membership implementation. Its direct calls are local functions defined in the same file (`rows`, `nse_prices`, `trading_days`, `month_end`, `prior_month`, `membership_at`, `independent_selection`, `main`) and file reads of:
- config/phase05_config.json
- audits/nse_trading_calendar_v3.csv
- data/raw/prices/download_manifest.csv
- data/reference/nifty50_baseline.csv
- data/reference/nifty50_membership.csv
- data/reference/security_identity_events.csv
- audits/phase05_top5_feasibility.csv

Primary-code import/call path: NONE FOUND.

However, the committed repository does not contain the generated `audits/phase1a_gate4_reproduction.csv` output, and the full historical price dataset needed to independently execute this reproduction is not present in the committed tree (only sample price files are present). Therefore the claimed 155-row / 31-date × 5 exact reproduction is UNVERIFIED in this R0 execution.

8. Capital feasibility:
The committed `docs/PHASE05_RETAIL_FEASIBILITY_EVIDENCE.md` reports:

| Capital | Unbuyable rebalances | Mean cash | Mean abs. weight deviation |
|---:|---:|---:|---:|
| Rs 20,000 | 21/31 | 26.43% | 5.29% |
| Rs 25,000 | 19/31 | 24.91% | 4.98% |
| Rs 50,000 | 7/31 | 13.05% | 2.61% |
| Rs 100,000 | 0/31 | 5.34% | 1.07% |

These are feasibility diagnostics, not performance results.

R0 specifically requires unbuyable slots and mean/median/max residual cash plus mean invested weight. Those exact fields are not present in the committed evidence artifact, and the underlying full Top-5 feasibility CSV is not committed. Therefore those requested R0 metrics are UNVERIFIED and were not invented.

## Result

**FAIL / BLOCKED — R0 hard stop.**

Blocking discrepancies:
1. Required historical commit `56d99fb55021e9935113af390e2216e89c57ffa0` is not found in the repository.
2. Current frozen-config SHA-256 is `9d7f1254bab1e492634c3093e22a916db45d5666c687f19ef277684c1c812a4f`, not the Blueprint claim `0059f964d2e5fa5f35e758210c61426f861bead352325db9297b7c281592646d`.
3. The repository's freeze manifest records a different config blob SHA from the current branch.
4. The requested G4 155-row output cannot be recomputed from the committed repository because the generated output and complete historical price inputs are absent.
5. Several required capital-feasibility R0 statistics cannot be recomputed from committed artifacts.

Per the Blueprint, any R0 mismatch blocks all later phases. No P2/P3/P4/P5/P7/P8/P9 work was started.

## Assumptions / UNVERIFIED

- The GitHub branch `phase1a-final-preflight` is treated as the repository state to verify because it is the identified preflight branch.
- GitHub cannot expose a local working tree's uncommitted changes; local clean/dirty state is therefore UNVERIFIED.
- G4 independence is a static-code PASS, not an executed 155-row reproduction.
- Capital feasibility values beyond those explicitly committed in `PHASE05_RETAIL_FEASIBILITY_EVIDENCE.md` remain UNVERIFIED.

## Discrepancies versus Blueprint

| Blueprint claim | Repository value | Status |
|---|---|---|
| Historical commit 56d99fb... exists | Not found | MISMATCH |
| Config SHA-256 0059f964... | 9d7f1254... | MISMATCH |
| 42 research-period transitions | 42 | MATCH |
| 16 official review events | 16 | MATCH |
| G4 = 155 rows / 31×5 | Output not committed; cannot recompute from committed inputs | UNVERIFIED |
| Capital feasibility complete at Rs20k/25k/50k/100k | Partial committed evidence only | UNVERIFIED |

## Risks not ruled out

- The current branch may have been advanced beyond the exact frozen state represented by the Blueprint.
- The missing historical commit may exist only in an inaccessible prior local clone or prior repository history, but it is not verifiable from the current GitHub repository.
- Missing full price artifacts prevent a fresh independent reconstruction of the 31 decision-date G4 result and the full capital-feasibility statistics.

## Reviewer should check hardest

1. Why the Blueprint names `56d99fb55021...` but the current repository has no such commit.
2. Why the current config hashes to `9d7f1254...` while the Blueprint claims `0059f964...`.
3. Whether `phase1a-final-preflight` is supposed to be based on the historical frozen state or on the later TRI-audit commits.
4. Whether the complete G4 and capital-feasibility artifacts should be restored/provided before any downstream preflight phase is allowed.

**No performance run was executed.**

