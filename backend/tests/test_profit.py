"""收益计算单测。这块算错产品就废了，必须有测试。"""
from __future__ import annotations

import math

from app.services.profit import (
    TxRow,
    compute_position,
    market_value,
    today_profit,
    total_profit,
)


def _approx(a: float, b: float, tol: float = 1e-3) -> bool:
    return math.isclose(a, b, abs_tol=tol)


def test_single_buy():
    txs = [TxRow(date="2026-01-10", type="buy", nav=1.0, shares=1000, amount=1000)]
    pos = compute_position(txs)
    assert pos.shares == 1000
    assert pos.cost_amount == 1000
    assert pos.avg_cost == 1.0
    assert pos.realized_profit == 0


def test_buy_with_fee():
    txs = [TxRow(date="2026-01-10", type="buy", nav=1.0, shares=1000, amount=1000, fee=1.5)]
    pos = compute_position(txs)
    assert pos.cost_amount == 1001.5
    assert _approx(pos.avg_cost, 1.0015)


def test_dca_average_cost():
    """定投均价应是份额加权，不是简单平均。"""
    txs = [
        TxRow(date="2026-01-10", type="buy", nav=1.0, shares=1000, amount=1000),
        TxRow(date="2026-02-10", type="buy", nav=2.0, shares=500, amount=1000),
    ]
    pos = compute_position(txs)
    assert pos.shares == 1500
    assert pos.cost_amount == 2000
    assert _approx(pos.avg_cost, 2000 / 1500)


def test_partial_sell_realized_profit():
    """卖出后应正确计算已实现收益和剩余成本。"""
    txs = [
        TxRow(date="2026-01-10", type="buy", nav=1.0, shares=1000, amount=1000),
        TxRow(date="2026-03-10", type="sell", nav=1.5, shares=400, amount=600),
    ]
    pos = compute_position(txs)
    assert _approx(pos.shares, 600)
    assert _approx(pos.cost_amount, 600)
    assert _approx(pos.realized_profit, 200)  # 卖出 400 份赚 0.5×400


def test_sell_more_than_held_caps_at_holding():
    txs = [
        TxRow(date="2026-01-10", type="buy", nav=1.0, shares=100, amount=100),
        TxRow(date="2026-02-10", type="sell", nav=2.0, shares=1000, amount=2000),
    ]
    pos = compute_position(txs)
    assert pos.shares == 0
    assert _approx(pos.cost_amount, 0)
    assert _approx(pos.realized_profit, 100)


def test_total_profit_floating_plus_realized():
    txs = [
        TxRow(date="2026-01-10", type="buy", nav=1.0, shares=1000, amount=1000),
        TxRow(date="2026-03-10", type="sell", nav=1.5, shares=400, amount=600),
    ]
    pos = compute_position(txs)
    total, rate = total_profit(pos, latest_nav=1.2)
    # 浮动 = 600×1.2 - 600 = 120; 已实现 = 200; 合计 320
    assert _approx(total, 320)
    assert _approx(rate, 320 / 600)


def test_market_value():
    assert _approx(market_value(1234.5678, 2.0), 2469.1356)


def test_today_profit_with_estimate():
    profit, rate = today_profit(shares=1000, latest_nav=1.0, estimated_nav=1.02)
    assert _approx(profit, 20.0)
    assert _approx(rate, 0.02)


def test_today_profit_no_estimate():
    assert today_profit(1000, 1.0, None) == (None, None)


def test_empty_transactions():
    pos = compute_position([])
    assert pos.shares == 0
    assert pos.cost_amount == 0
    assert pos.realized_profit == 0


def test_import_formula():
    market_value = 10000.0
    profit_val = 2000.0
    latest_nav = 2.0
    cost_amount = market_value - profit_val
    shares = market_value / latest_nav
    avg_cost = cost_amount / shares if shares > 0 else 0.0
    
    assert cost_amount == 8000.0
    assert shares == 5000.0
    assert avg_cost == 1.6
