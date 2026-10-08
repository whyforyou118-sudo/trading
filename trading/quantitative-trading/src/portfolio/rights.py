"""Rights-entitlement handling for the Phase 1A frozen V6 policy.

Policy:
- Entitlements are based on parent shares held on the entitlement date.
- Fractional entitlements are ignored; no synthetic additional subscription.
- REs are renounced (sold) at the first actual tradable session's raw open.
- The date-effective delivery cost model applies the frozen 0.10% slippage as
  an explicit cost. The ledger trade price remains the raw open.
- Partly-paid rights are not subscribed, so no later calls are due.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .costs import DeliveryCostModel


@dataclass(frozen=True)
class RightsEntitlement:
    date: str
    parent_symbol: str
    re_symbol: str
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if not self.parent_symbol or not self.re_symbol:
            raise ValueError("rights symbols cannot be empty")
        try:
            date.fromisoformat(self.date)
        except (TypeError, ValueError) as exc:
            raise ValueError("rights entitlement date must be ISO YYYY-MM-DD") from exc
        if (isinstance(self.numerator, bool) or isinstance(self.denominator, bool)
                or self.numerator <= 0 or self.denominator <= 0
                or int(self.numerator) != self.numerator
                or int(self.denominator) != self.denominator):
            raise ValueError("rights ratio terms must be positive whole numbers")

    def quantity(self, parent_shares: int) -> int:
        if isinstance(parent_shares, bool) or parent_shares < 0 or int(parent_shares) != parent_shares:
            raise ValueError("parent_shares must be a non-negative whole number")
        # Registered issuer terms ignore fractional entitlements; do not invent
        # cash-in-lieu or additional subscription shares.
        return (int(parent_shares) * self.numerator) // self.denominator


@dataclass(frozen=True)
class RightsRenunciation:
    """Sale instruction for an entitlement on its first tradable session.

    build_trade uses the raw exchange open as Trade.price and books slippage
    as a transaction cost. execution_price is retained only as a legacy
    effective-price diagnostic; do not combine it with build_trade because
    that would double-count slippage.
    """
    entitlement: RightsEntitlement
    first_tradable_date: str
    first_tradable_open: float
    slippage_pct: float = 0.001

    def __post_init__(self) -> None:
        try:
            trade_date = date.fromisoformat(self.first_tradable_date)
        except (TypeError, ValueError) as exc:
            raise ValueError("first_tradable_date must be ISO YYYY-MM-DD") from exc
        entitlement_date = date.fromisoformat(self.entitlement.date)
        if trade_date <= entitlement_date:
            raise ValueError("first tradable date must follow the entitlement date")
        if not isfinite(float(self.first_tradable_open)) or self.first_tradable_open <= 0:
            raise ValueError("first_tradable_open must be finite and positive")
        if not isfinite(float(self.slippage_pct)) or self.slippage_pct < 0:
            raise ValueError("slippage_pct must be finite and non-negative")

    def execution_price(self) -> float:
        """Legacy diagnostic: raw open less slippage, not a ledger trade price."""
        return float(self.first_tradable_open) * (1.0 - float(self.slippage_pct))

    def build_trade(self, parent_shares: int, cost_model: "DeliveryCostModel"):
        """Return the costed SELL trade at raw open, or None for zero entitlement."""
        from .accounting import Trade

        quantity = self.entitlement.quantity(parent_shares)
        if quantity == 0:
            return None
        gross = quantity * float(self.first_tradable_open)
        costs = cost_model.costs(
            date.fromisoformat(self.first_tradable_date),
            "SELL",
            gross,
            scrips_sold=1,
            slippage=self.slippage_pct,
        )
        return Trade(
            date=self.first_tradable_date,
            symbol=self.entitlement.re_symbol,
            side="SELL",
            shares=quantity,
            price=float(self.first_tradable_open),
            costs=costs,
        )
