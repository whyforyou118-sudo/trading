from src.portfolio.accounting import CostBreakdown, PortfolioState, Trade, RightsEntitlement as LedgerRightsEntitlement
from src.portfolio.rights import RightsEntitlement, RightsRenunciation


def test_rights_entitlement_rounds_down():
    event = RightsEntitlement("2024-07-27", "TATACONSUM", "TATACON-RE", 1, 26)
    assert event.quantity(25) == 0
    assert event.quantity(26) == 1
    assert event.quantity(51) == 1
    assert event.quantity(52) == 2


def test_grasim_entitlement():
    event = RightsEntitlement("2024-01-10", "GRASIM", "GRASIM-RE", 6, 179)
    assert event.quantity(29) == 0
    assert event.quantity(30) == 1
    assert event.quantity(358) == 12


def test_adani_entitlement():
    event = RightsEntitlement("2025-11-17", "ADANIENT", "ADANI-RE", 3, 25)
    assert event.quantity(8) == 0
    assert event.quantity(9) == 1
    assert event.quantity(25) == 3


def test_renunciation_uses_first_open_and_slippage():
    event = RightsEntitlement("2024-01-10", "GRASIM", "GRASIM-RE", 6, 179)
    renounce = RightsRenunciation(event, "2024-01-17", 320.05)
    assert round(renounce.execution_price(), 8) == round(320.05 * 0.999, 8)


def test_ledger_integrates_rights_entitlement_path_conditionally():
    from src.portfolio.accounting import apply_ledger
    event = LedgerRightsEntitlement("2024-07-27", "TATACONSUM", "TATACON-RE", 1, 26)
    state = apply_ledger(25000.0, [event])
    assert state.shares("TATACON-RE") == 0

    state = apply_ledger(25000.0, [event, Trade("2024-08-05", "TATACON-RE", "SELL", 1, 303.00)])
    assert state.shares("TATACON-RE") == 0


def test_path_conditional_re_sale():
    event = RightsEntitlement("2024-01-10", "GRASIM", "GRASIM-RE", 6, 179)
    parent_shares = 358
    re_shares = event.quantity(parent_shares)
    assert re_shares == 12

    state = PortfolioState(cash=25000.0, positions={"GRASIM": parent_shares})
    state.positions["GRASIM-RE"] = re_shares

    gross = re_shares * 320.05
    costs = CostBreakdown(
        stt=gross * 0.000625,
        transaction_charges=gross * 0.0000322,
        sebi=gross * 0.000001,
        gst=(gross * 0.0000322 + gross * 0.000001) * 0.18,
        dp_charge=13.0,
        slippage=gross * 0.001,
    )
    state.apply_trade(Trade(
        "2024-01-17", "GRASIM-RE", "SELL", re_shares, 320.05, costs
    ))
    assert state.shares("GRASIM-RE") == 0
    assert state.cash < 25000.0 + gross
    assert state.cash > 25000.0


def test_no_parent_holding_means_no_re():
    event = RightsEntitlement("2024-01-10", "GRASIM", "GRASIM-RE", 6, 179)
    assert event.quantity(0) == 0
