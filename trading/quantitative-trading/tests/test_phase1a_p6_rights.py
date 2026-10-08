from datetime import date

from src.audit.phase1a_p6_rights_treatment import EVENTS


def test_p6_rights_issue_prices_and_factors_are_frozen():
    got = {
        e.symbol: (
            e.ex_date,
            e.record_date,
            e.a,
            e.b,
            e.face_value,
            e.premium,
            e.issue_price,
            e.adjustment_factor,
        )
        for e in EVENTS
    }

    assert got["GRASIM"] == (
        date(2024, 1, 10), date(2024, 1, 10),
        6, 179, 2.0, 1810.0, 1812.0, 0.996040
    )
    assert got["TATACONSUM"] == (
        date(2024, 7, 26), date(2024, 7, 27),
        1, 26, 1.0, 817.0, 818.0, 0.987723
    )
    assert got["ADANIENT"] == (
        date(2025, 11, 17), date(2025, 11, 17),
        3, 25, 1.0, 1799.0, 1800.0, 0.970366
    )
