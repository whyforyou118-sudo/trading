"""P6 rights-event resolution for the frozen V6 research path.

This audit distinguishes:
1. NSE corporate-action wording (premium),
2. verified total issue price, and
3. the NSE rights adjustment factor used for the signal series.

It intentionally does NOT invent a retail portfolio treatment for Rights
Entitlements (REs). That remains a separate gate because an exact ₹25K
implementation must specify whether REs are subscribed, renounced/sold, or
allowed to lapse.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RightsEvent:
    symbol: str
    ex_date: date
    record_date: date
    a: int
    b: int
    face_value: float
    premium: float
    issue_price: float
    adjustment_factor: float
    benefit_per_old_share: float
    source: str


EVENTS = (
    RightsEvent(
        "GRASIM", date(2024, 1, 10), date(2024, 1, 10),
        6, 179, 2.0, 1810.0, 1812.0, 0.996040, 8.174594595,
        "NSE F&O Circular FAOP60188 / GRASIM Letter of Offer",
    ),
    RightsEvent(
        "TATACONSUM", date(2024, 7, 26), date(2024, 7, 27),
        1, 26, 1.0, 817.0, 818.0, 0.987723, 15.02222222,
        "NSE F&O Circular FAOP63078 / Tata Consumer filing",
    ),
    RightsEvent(
        "ADANIENT", date(2025, 11, 17), date(2025, 11, 17),
        3, 25, 1.0, 1799.0, 1800.0, 0.970366, 73.73571429,
        "NSE F&O Circular FAOP71284 / Adani Letter of Offer",
    ),
)


def main() -> int:
    print("PHASE 1A P6 — RIGHTS TREATMENT AUDIT")
    print("Verified issue prices and NSE adjustment factors:")
    print()

    for e in EVENTS:
        print(
            f"{e.ex_date.isoformat()} | {e.symbol} | "
            f"ratio={e.a}:{e.b} | premium={e.premium:.2f} | "
            f"issue_price={e.issue_price:.2f} | "
            f"factor={e.adjustment_factor:.6f} | "
            f"benefit_per_old_share={e.benefit_per_old_share:.8f} | "
            f"record_date={e.record_date.isoformat()}"
        )

    print()
    print("P6 RIGHTS PORTFOLIO DIAGNOSTIC")
    print("=" * 72)
    requirements = (
        ("signal_factor", "PASS", "Verified NSE rights adjustment factor is available."),
        ("re_price_data", "PASS", "Official NSE RE historical rows are archived for all three events."),
        ("re_first_tradable_open", "PASS", "First tradable session/open is identified from archived NSE rows."),
        ("entitlement_rule", "BLOCKED", "No production rule calculates integer RE entitlement from parent shares."),
        ("fractional_entitlement_rule", "BLOCKED", "No issuer-specific fractional-entitlement treatment is implemented."),
        ("portfolio_policy", "BLOCKED", "Subscribe/renounce/lapse policy is not frozen for the exact ₹25K estimand."),
        ("re_transaction_costs", "BLOCKED", "Applicable RE transaction costs are not yet validated and implemented."),
        ("ledger_integration", "BLOCKED", "The accounting ledger has no Rights Entitlement event or RE sale path."),
        ("path_conditional_test", "BLOCKED", "No test proves treatment applies only when parent shares were actually held."),
    )

    blocked = 0
    for event in EVENTS:
        print(f"{event.symbol} | ex_date={event.ex_date.isoformat()} | record_date={event.record_date.isoformat()}")
        for name, status, detail in requirements:
            print(f"  {status:<7} {name:<28} {detail}")
            blocked += status == "BLOCKED"
        print()

    print("SIGNAL TREATMENT: PASS — verified NSE rights adjustment factors are available.")
    print(f"PORTFOLIO TREATMENT: BLOCKED — {blocked} unmet requirement checks across {len(EVENTS)} events.")
    print("STATUS: BLOCKED — no performance run is authorized until portfolio-side rights treatment is implemented and tested.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
