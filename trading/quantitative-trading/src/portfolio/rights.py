"""Rights Entitlement accounting for the Phase 1A frozen V6 portfolio policy.

Policy:
- REs are path-conditional on parent shares held at the record date.
- Fractional entitlements are ignored; no synthetic additional subscription.
- The frozen portfolio treatment is RENOUNCE_AT_FIRST_TRADABLE_OPEN.
- The RE is sold on its first actual tradable session at that session's open.
- The caller supplies the validated historical open and applicable costs.
- Partly-paid rights require no future call because the RE is renounced before
  subscription/allotment.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


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
        if (isinstance(self.numerator, bool) or isinstance(self.denominator, bool)
                or self.numerator <= 0 or self.denominator <= 0
                or int(self.numerator) != self.numerator
                or int(self.denominator) != self.denominator):
            raise ValueError("rights ratio terms must be positive whole numbers")

    def quantity(self, parent_shares: int) -> int:
        if isinstance(parent_shares, bool) or parent_shares < 0 or int(parent_shares) != parent_shares:
            raise ValueError("parent_shares must be a non-negative whole number")
        # Issuer terms for all three Phase 1A events ignore fractional
        # entitlements; no additional subscription is modeled.
        return (int(parent_shares) * self.numerator) // self.denominator


@dataclass(frozen=True)
class RightsRenunciation:
    entitlement: RightsEntitlement
    first_tradable_date: str
    first_tradable_open: float
    slippage_pct: float = 0.001

    def __post_init__(self) -> None:
        if not self.first_tradable_date:
            raise ValueError("first_tradable_date cannot be empty")
        if not isfinite(float(self.first_tradable_open)) or self.first_tradable_open <= 0:
            raise ValueError("first_tradable_open must be finite and positive")
        if not isfinite(float(self.slippage_pct)) or self.slippage_pct < 0:
            raise ValueError("slippage_pct must be finite and non-negative")

    def execution_price(self) -> float:
        return self.first_tradable_open * (1.0 - self.slippage_pct)
