from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from portfolio.costs import DeliveryCostModel

ROOT = Path(__file__).resolve().parents[1]


def test_date_effective_cost_rows_cover_research_period():
    model = DeliveryCostModel.from_csv(ROOT / "data/reference/zerodha_delivery_cost_schedule.csv")
    assert model.row(date(2018, 1, 2)).transaction_charge_pct == 0.00345
    assert model.row(date(2024, 10, 1)).transaction_charge_pct == 0.00297
    assert model.row(date(2025, 12, 31)).dp_per_scrip == 13.0


def test_buy_and_sell_have_correct_side_specific_charges():
    model = DeliveryCostModel.from_csv(ROOT / "data/reference/zerodha_delivery_cost_schedule.csv")
    buy = model.costs(date(2025, 1, 2), "BUY", 10000.0, slippage=0.001)
    sell = model.costs(date(2025, 1, 2), "SELL", 10000.0, scrips_sold=1, slippage=0.001)
    assert buy.stamp_duty > 0
    assert sell.stamp_duty == 0
    assert buy.dp_charge == 0
    assert sell.dp_charge == 13.0
    assert buy.slippage == sell.slippage == 10.0
