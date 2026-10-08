# Phase 1B Path-Conditional Gate Decision — Britannia Debentures

**Decision ID:** `PHASE1B-BRITANNIA-PATH-GATE-V1`  
**Scope:** Frozen V6 primary strategy only  
**Status:** IMPLEMENTATION DECISION — MUST BE VERIFIED BY THE AUTOMATED AUDIT  
**Run 1:** NOT AUTHORIZED

## Decision

Do not wait for an email response before continuing Phase 1 implementation. External confirmation remains optional follow-up evidence, not a development dependency.

The frozen V6 blueprint requires path-conditional corporate-action handling. The Britannia debenture coupon cashflows remain unresolved for a general-purpose historical accounting ledger; they must not be fabricated or represented as verified. However, whether those amounts block the frozen V6 performance run should be decided by an automated path-relevance audit, not by assuming every event affects every strategy.

The signal layer and audits are versioned separately:
- `src/strategy/corporate_action_signal.py` implements point-in-time signal-price adjustment without modifying raw execution prices.
- `src/audit/phase1b_britannia_signal_adjustment_audit.py` compares raw momentum, the provisional face-value primary policy, and the listing-only sensitivity for all frozen decision dates. It must not overwrite the existing raw selection evidence.
- `src/audit/phase1b_britannia_path_relevance.py` checks entitlement holdings and every overlapping formation window. An overlap is acceptable only when the primary adjustment is evidenced for that exact formation end, the listing-only sensitivity passes, and the recomputed raw Top-5 still matches the existing raw selection artifact.

The signal adjustment factor is `raw parent equity close on ex-date / (raw parent equity close on ex-date + distribution value)`. The primary policy uses the versioned provisional face values (₹30 and ₹29), which are assumptions and not verified fair values. The listing-only sensitivity uses the exact raw debenture close by ISIN on the first tradable date and does not use that quote before it becomes observable.

The path audit must check all decision dates, not just dates when BRITANNIA was selected. If the new signal audit and path audit pass, the conclusion is limited to this: no Britannia debenture entitlement cashflow is owed by the frozen V6 portfolio at those ex-dates, and the detected signal-window effects have an explicit, point-in-time adjustment with a required listing-only sensitivity. This does **not** validate the debenture's fair value, verify coupon values, complete the generic accounting ledger, or authorize performance by itself.

If the signal audit or path audit fails, the Britannia event treatment remains a performance blocker and must be resolved before Run 1.

## Required verification

- Run the dedicated path-relevance tests.
- Run the full regression suite.
- Inspect the generated `audits/phase1b_britannia_path_relevance.json` artifact.
- Complete the listing-only sensitivity and all remaining Phase 1B accounting / preflight gates.
- Create a clean final freeze and manifest before considering Run 1.

This is a scope clarification for the frozen V6 strategy and does not modify any strategy parameters, data, or the protected V6 baseline. The general-purpose event ledger must continue to record unresolved coupon amounts as unresolved.
