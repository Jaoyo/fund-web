"""收益计算 —— 份额加权成本法。

核心规则：
- 买入：份额增加，成本增加（成本 = 成交金额 + 费用）
- 卖出：份额减少，成本按"卖出份额 / 卖出前总份额"比例摊销
- 卖出回款 = 卖出份额 × 成交净值 - 费用
- 已实现收益 = 累计卖出回款 - 累计摊销成本
- 持仓收益 = 当前市值 - 剩余成本 + 已实现收益

注：T+1 确认日差异由调用方控制；这里假设 transactions 表的 date 即份额生效日。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class TxRow:
    """profit 计算只关心这几个字段，方便单测脱离 DB。"""

    date: str
    type: str  # 'buy', 'sell', 或 'import'（导入持仓，当天即生效）
    nav: float
    shares: float
    amount: float
    fee: float = 0.0


@dataclass
class PositionResult:
    shares: float
    cost_amount: float  # 剩余成本（已扣摊销）
    avg_cost: float  # 持仓均价
    realized_profit: float  # 已实现收益


def compute_position(txs: Iterable[TxRow]) -> PositionResult:
    """对一只基金的所有交易，按时间顺序计算当前持仓状态。"""
    # 二级排序：同一天时，买入（buy/import）排在卖出（sell）之前，避免因顺序问题吞掉卖出份额
    sorted_txs = sorted(txs, key=lambda t: (t.date, 0 if t.type in ("buy", "import") else 1))

    shares = 0.0
    cost = 0.0
    realized = 0.0

    for t in sorted_txs:
        # 待确认交易（未知价）不计入当前持仓和成本
        if t.nav == 0.0:
            continue

        if t.type in ("buy", "import"):
            shares += t.shares
            cost += t.amount + t.fee
        elif t.type == "sell":
            if shares <= 0:
                continue
            sell_shares = min(t.shares, shares)
            ratio = sell_shares / shares
            cost_out = cost * ratio
            proceeds = sell_shares * t.nav - t.fee
            realized += proceeds - cost_out
            cost -= cost_out
            shares -= sell_shares
        else:
            continue

    avg_cost = cost / shares if shares > 1e-9 else 0.0
    return PositionResult(
        shares=round(shares, 4),
        cost_amount=round(cost, 4),
        avg_cost=round(avg_cost, 6),
        realized_profit=round(realized, 4),
    )


def market_value(shares: float, latest_nav: float) -> float:
    return round(shares * latest_nav, 4)


def total_profit(position: PositionResult, latest_nav: float) -> tuple[float, float]:
    """返回 (累计收益, 累计收益率)。

    累计收益 = 浮动盈亏 + 已实现盈亏
    收益率分母用"累计投入"近似：剩余成本 + 已实现部分对应的原始成本不易回溯，
    所以用 (cost_amount + max(realized, 0)) 略偏保守；个人自用够了。
    """
    floating = position.shares * latest_nav - position.cost_amount
    total = floating + position.realized_profit
    denom = position.cost_amount if position.cost_amount > 1e-9 else 1.0
    rate = total / denom
    return round(total, 4), round(rate, 6)


def today_profit(
    shares: float, latest_nav: float, estimated_nav: float | None
) -> tuple[float | None, float | None]:
    """基于盘中估值算今日预估收益。盘后估值不可用时返回 (None, None)。"""
    if estimated_nav is None or shares <= 0 or latest_nav <= 0:
        return None, None
    profit = shares * (estimated_nav - latest_nav)
    rate = (estimated_nav - latest_nav) / latest_nav
    return round(profit, 4), round(rate, 6)

def actual_daily_profit(
    shares: float, today_nav: float, yesterday_nav: float
) -> tuple[float, float]:
    """基于两日真实净值计算单日实际确认收益。"""
    if shares <= 0 or yesterday_nav <= 0:
        return 0.0, 0.0
    profit = shares * (today_nav - yesterday_nav)
    rate = (today_nav - yesterday_nav) / yesterday_nav
    return round(profit, 4), round(rate, 6)
