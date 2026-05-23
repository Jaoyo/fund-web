"""智能建议：基于历史净值的 4 个统计指标。

1. 历史百分位 (3 年)：当前净值在过去 3 年的分位数
2. MA 偏离度：现价相对 250 日均线的偏离百分比
3. 最大回撤：从买入后最高点的回撤
4. 止盈线：收益率达到阈值
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models.advice import AdviceSignal, FundAdvice
from ..models.fund import NavRecord


# 阈值常量。个人自用，可以直接改。
PERCENTILE_BUY_BELOW = 0.20
PERCENTILE_SELL_ABOVE = 0.80
MA_WINDOW = 250
MA_DEVIATION_BUY_BELOW = -0.10
MA_DEVIATION_SELL_ABOVE = 0.15
DRAWDOWN_WARN = -0.10
PROFIT_TAKE_RATE = 0.20


@dataclass
class _Metrics:
    percentile: float | None
    ma_deviation: float | None
    max_drawdown: float | None


def compute_metrics(navs: list[NavRecord]) -> _Metrics:
    if not navs:
        return _Metrics(None, None, None)

    asc = sorted(navs, key=lambda n: n.date)
    values = [n.nav for n in asc if n.nav > 0]
    if not values:
        return _Metrics(None, None, None)

    latest = values[-1]

    # 历史百分位
    sorted_vals = sorted(values)
    below = sum(1 for v in sorted_vals if v < latest)
    percentile = below / len(sorted_vals)

    # MA 偏离度
    window = values[-MA_WINDOW:] if len(values) >= MA_WINDOW else values
    ma = sum(window) / len(window) if window else None
    ma_deviation = (latest - ma) / ma if ma else None

    # 最大回撤（从最高点）
    peak = values[0]
    max_dd = 0.0
    for v in values:
        if v > peak:
            peak = v
        dd = (v - peak) / peak
        if dd < max_dd:
            max_dd = dd

    return _Metrics(
        percentile=round(percentile, 4),
        ma_deviation=round(ma_deviation, 4) if ma_deviation is not None else None,
        max_drawdown=round(max_dd, 4),
    )


def build_advice(
    fund_code: str,
    fund_name: str,
    navs: list[NavRecord],
    profit_rate: float | None = None,
    held_drawdown: float | None = None,
) -> FundAdvice:
    """profit_rate / held_drawdown 由调用方根据持仓数据传入。"""
    m = compute_metrics(navs)
    signals: list[AdviceSignal] = []

    if m.percentile is not None:
        if m.percentile <= PERCENTILE_BUY_BELOW:
            signals.append(
                AdviceSignal(
                    name="历史低位",
                    level="buy",
                    message=f"当前净值在历史 {m.percentile:.0%} 分位，处于低位",
                    value=m.percentile,
                )
            )
        elif m.percentile >= PERCENTILE_SELL_ABOVE:
            signals.append(
                AdviceSignal(
                    name="历史高位",
                    level="sell",
                    message=f"当前净值在历史 {m.percentile:.0%} 分位，处于高位",
                    value=m.percentile,
                )
            )

    if m.ma_deviation is not None:
        if m.ma_deviation <= MA_DEVIATION_BUY_BELOW:
            signals.append(
                AdviceSignal(
                    name="均线偏离",
                    level="buy",
                    message=f"相对 {MA_WINDOW} 日均线偏离 {m.ma_deviation:.1%}，超跌",
                    value=m.ma_deviation,
                )
            )
        elif m.ma_deviation >= MA_DEVIATION_SELL_ABOVE:
            signals.append(
                AdviceSignal(
                    name="均线偏离",
                    level="sell",
                    message=f"相对 {MA_WINDOW} 日均线偏离 {m.ma_deviation:.1%}，超买",
                    value=m.ma_deviation,
                )
            )

    if held_drawdown is not None and held_drawdown <= DRAWDOWN_WARN:
        signals.append(
            AdviceSignal(
                name="持仓回撤",
                level="watch",
                message=f"自买入后回撤 {held_drawdown:.1%}，注意风险",
                value=held_drawdown,
            )
        )

    if profit_rate is not None and profit_rate >= PROFIT_TAKE_RATE:
        signals.append(
            AdviceSignal(
                name="止盈触发",
                level="sell",
                message=f"累计收益率 {profit_rate:.1%}，可考虑止盈",
                value=profit_rate,
            )
        )

    if not signals:
        signals.append(
            AdviceSignal(name="持有", level="info", message="无明显买卖信号")
        )

    return FundAdvice(
        fund_code=fund_code,
        fund_name=fund_name,
        signals=signals,
        percentile=m.percentile,
        ma_deviation=m.ma_deviation,
        max_drawdown=m.max_drawdown,
        profit_rate=profit_rate,
    )
