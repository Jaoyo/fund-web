from __future__ import annotations

from fastapi import APIRouter

from ..db import get_conn
from ..models.holding import HoldingsSummary, Position
from ..response import ok
from ..services import nav_cache, profit

router = APIRouter(prefix="/holdings", tags=["holdings"])


@router.get("")
async def list_holdings() -> dict:
    """所有持仓汇总。聚合 transactions，按 fund_code 分组算份额/成本/收益。"""
    with get_conn() as conn:
        codes = [
            r["fund_code"]
            for r in conn.execute(
                "SELECT DISTINCT fund_code FROM transactions"
            ).fetchall()
        ]
        fund_names = {
            r["code"]: r["name"]
            for r in conn.execute("SELECT code, name FROM funds").fetchall()
        }

    positions: list[Position] = []
    total_market = 0.0
    total_cost = 0.0
    total_today = 0.0

    for code in codes:
        with get_conn() as conn:
            tx_rows = conn.execute(
                "SELECT date, type, nav, shares, amount, fee "
                "FROM transactions WHERE fund_code = ? ORDER BY date",
                (code,),
            ).fetchall()

        txs = [
            profit.TxRow(
                date=r["date"],
                type=r["type"],
                nav=r["nav"],
                shares=r["shares"],
                amount=r["amount"],
                fee=r["fee"],
            )
            for r in tx_rows
        ]
        pos = profit.compute_position(txs)
        if pos.shares <= 1e-6:
            continue

        quote = await nav_cache.get_quote(code)
        latest_nav = quote.nav if quote else 0.0
        latest_date = quote.nav_date if quote else ""

        market = profit.market_value(pos.shares, latest_nav)
        gain, gain_rate = profit.total_profit(pos, latest_nav)
        today_p, today_r = profit.today_profit(
            pos.shares, latest_nav, quote.estimated_nav if quote else None
        )

        positions.append(
            Position(
                fund_code=code,
                fund_name=fund_names.get(code, quote.name if quote else code),
                shares=pos.shares,
                cost_amount=pos.cost_amount,
                avg_cost=pos.avg_cost,
                market_value=market,
                profit=gain,
                profit_rate=gain_rate,
                today_profit=today_p,
                today_profit_rate=today_r,
                latest_nav=latest_nav,
                latest_nav_date=latest_date,
                estimated_nav=quote.estimated_nav if quote else None,
                estimated_growth=quote.estimated_growth if quote else None,
            )
        )

        total_market += market
        total_cost += pos.cost_amount
        if today_p is not None:
            total_today += today_p

    total_profit_val = total_market - total_cost
    rate = total_profit_val / total_cost if total_cost > 1e-6 else 0.0

    summary = HoldingsSummary(
        total_market_value=round(total_market, 4),
        total_cost=round(total_cost, 4),
        total_profit=round(total_profit_val, 4),
        total_profit_rate=round(rate, 6),
        today_profit=round(total_today, 4),
        positions=positions,
    )
    return ok(summary.model_dump())
