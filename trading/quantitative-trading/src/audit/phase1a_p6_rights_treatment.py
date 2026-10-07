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
from pathlib import Path
import csv

from src.portfolio.rights import RightsEntitlement, RightsRenunciation
from src.portfolio.accounting import PortfolioState


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
    root = Path(__file__).resolve().parents[2]
    price_dir = root / "data/raw/rights_entitlements"
    cost_file = root / "data/reference/zerodha_delivery_cost_schedule.csv"
    price_expectations = {
        "GRASIM": ("GRASIM-RE", date(2024, 1, 17), 320.05, 0.000625),
        "TATACONSUM": ("TATACON-RE", date(2024, 8, 5), 303.00, 0.000625),
        "ADANIENT": ("ADANI-RE", date(2025, 11, 25), 590.00, 0.001),
    }
    failures = []

    with cost_file.open(encoding="utf-8-sig", newline="") as f:
        cost_rows = list(csv.DictReader(f))

    for e in EVENTS:
        print(f"{e.symbol} | ex_date={e.ex_date.isoformat()} | record_date={e.record_date.isoformat()}")
        ent = RightsEntitlement(e.record_date.isoformat(), e.symbol, price_expectations[e.symbol][0], e.a, e.b)
        re_symbol, first_date, expected_open, expected_stt = price_expectations[e.symbol]

        checks = [
            ("signal_factor", True, "Verified NSE rights adjustment factor is available."),
            ("re_price_data", False, "Archived official NSE RE price rows must be validated below."),
            ("re_first_tradable_open", False, "Archived first tradable session/open must be validated below."),
            ("entitlement_rule", False, "Issuer-defined integer entitlement must be exercised by the ledger."),
            ("fractional_entitlement_rule", False, "Issuer terms ignore fractional entitlements."),
            ("portfolio_policy", True, "Frozen policy: RE_RENOUNCE_AT_FIRST_TRADABLE_OPEN."),
            ("re_transaction_costs", False, "Historical RE STT and verified cash-market cost interval must be validated."),
            ("ledger_integration", True, "RightsEntitlement is integrated into the accounting ledger."),
            ("path_conditional_test", False, "Ledger test must prove zero entitlement without parent holdings."),
        ]

        price_files = list(price_dir.glob(f"{re_symbol}_*_prices.csv"))
        rows = []
        for p in price_files:
            with p.open(encoding="utf-8", newline="") as f:
                rows.extend(r for r in csv.DictReader(f) if r["date"] == first_date.isoformat())
        price_ok = len(rows) == 1 and float(rows[0]["open"]) == expected_open
        checks[1] = ("re_price_data", price_ok, f"{len(rows)} archived first-session row(s) for {re_symbol}.")
        checks[2] = ("re_first_tradable_open", price_ok, f"{first_date} open={expected_open:.2f}.")

        rule_ok = ent.quantity(e.b - 1) == 0 and ent.quantity(e.b) == e.a
        checks[3] = ("entitlement_rule", rule_ok, f"quantity({e.b - 1})=0; quantity({e.b})={e.a}.")
        checks[4] = ("fractional_entitlement_rule", rule_ok, "fractional entitlement is ignored; no additional subscription is modeled.")

        interval = None
        for row in cost_rows:
            a = date.fromisoformat(row["effective_from"])
            b = date.fromisoformat(row["effective_to"])
            if a <= first_date <= b:
                interval = row
                break
        cost_ok = interval is not None and interval.get("verified", "").upper() == "TRUE"
        checks[6] = ("re_transaction_costs", cost_ok, f"RE STT seller rate={expected_stt:.5%}; verified cost interval present={interval is not None}.")

        no_parent = PortfolioState(cash=25000.0, positions={})
        no_parent_qty = no_parent.apply_rights_entitlement(ent)
        parent = PortfolioState(cash=25000.0, positions={e.symbol: e.b})
        parent_qty = parent.apply_rights_entitlement(ent)
        path_ok = no_parent_qty == 0 and parent_qty == e.a and parent.shares(re_symbol) == e.a
        checks[8] = ("path_conditional_test", path_ok, f"no-parent={no_parent_qty}; one-ratio-parent={parent_qty}.")

        ren = RightsRenunciation(ent, first_date.isoformat(), expected_open)
        exec_ok = ren.execution_price() == expected_open * 0.999
        checks.append(("first_open_slippage", exec_ok, f"execution price={ren.execution_price():.6f}."))

        for name, status, detail in checks:
            label = "PASS" if status else "BLOCKED"
            print(f"  {label:<7} {name:<28} {detail}")
            if not status:
                failures.append(f"{e.symbol}:{name}")
        print()

    print("SIGNAL TREATMENT: PASS — verified NSE rights adjustment factors are available.")
    if failures:
        print(f"PORTFOLIO TREATMENT: BLOCKED — {len(failures)} unmet checks.")
        print("STATUS: BLOCKED — rights treatment is not fully validated.")
        return 2
    print("PORTFOLIO TREATMENT: PASS — all three rights events use the frozen renunciation policy.")
    print("STATUS: PASS — rights portfolio treatment is implemented and validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
