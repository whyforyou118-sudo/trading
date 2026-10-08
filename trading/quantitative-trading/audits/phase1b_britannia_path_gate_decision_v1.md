# Phase 1B Path-Conditional Gate Decision — Britannia Debentures

**Decision ID:** `PHASE1B-BRITANNIA-PATH-GATE-V1`  
**Scope:** Frozen V6 primary strategy only  
**Status:** IMPLEMENTATION DECISION — MUST BE VERIFIED BY THE AUTOMATED AUDIT  
**Run 1:** NOT AUTHORIZED

## Decision

Do not wait for an email response before continuing Phase 1 implementation. External confirmation remains optional follow-up evidence, not a development dependency.

The frozen V6 blueprint requires path-conditional corporate-action handling. The Britannia debenture coupon cashflows remain unresolved for a general-purpose historical accounting ledger; they must not be fabricated or represented as verified. However, whether those amounts block the frozen V6 performance run should be decided by an automated path-relevance audit, not by assuming every event affects every strategy.

The new audit script `src/audit/phase1b_britannia_path_relevance.py` checks the frozen Phase 1B selection audit for:
1. Any BRITANNIA execution position on or before either debenture ex-date.
2. Either ex-date falling inside any quarterly decision's 12-month formation window after the 1-month skip, including decisions where BRITANNIA was not selected.
3. An explicit report that does not authorize Run 1.

If the script passes on the frozen selection artifact, its conclusion is limited: the unresolved coupon amounts and valuation events are path-conditionally irrelevant to the frozen V6 primary strategy because no eligible BRITANNIA position exists at entitlement and neither ex-date overlaps any quarterly momentum formation window. The audit must check all decision dates, not just dates when BRITANNIA was selected. This does **not** validate the coupon values, complete the generic accounting ledger, or authorize performance by itself.

If the audit fails, the Britannia event treatment remains a performance blocker and must be resolved before Run 1.

## Required verification

- Run the dedicated path-relevance tests.
- Run the full regression suite.
- Inspect the generated `audits/phase1b_britannia_path_relevance.json` artifact.
- Complete the listing-only sensitivity and all remaining Phase 1B accounting / preflight gates.
- Create a clean final freeze and manifest before considering Run 1.

This is a scope clarification for the frozen V6 strategy and does not modify any strategy parameters, data, or the protected V6 baseline. The general-purpose event ledger must continue to record unresolved coupon amounts as unresolved.
