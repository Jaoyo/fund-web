from __future__ import annotations

from fastapi import APIRouter

from ..db import get_conn
from ..response import ok
from ..services import advisor, nav_cache, profit

router = APIRouter(prefix="/advice", tags=["advice"])


@router.get("")
async def list_advice(days: int = 750) -> dict:
    """所有持仓基金的建议汇总。"""
    with get_conn() as conn:
        codes = [
            r["code"]
            for r in conn.execute(
                "SELECT f.code FROM funds f "
                "JOIN (SELECT DISTINCT fund_code FROM transactions) t ON f.code = t.fund_code "
                "ORDER BY f.sort_order ASC, f.code ASC"
            ).fetchall()
        ]

    import asyncio
    
    tasks = [_build_one(code, days) for code in codes]
    advices = await asyncio.gather(*tasks)
    
    results = [a for a in advices if a is not None]
            
    # 保证持仓的基金在前，未持仓（已清仓/仅关注）的基金在后，且内部保留原来的 sort_order
    results.sort(key=lambda x: x["profit_rate"] is None)
    return ok(results)


@router.get("/{code}")
async def get_advice(code: str, days: int = 750) -> dict:
    """单基金详细指标。即使没持仓也能查（用于决定要不要建仓）。"""
    advice = await _build_one(code, days)
    if advice is None:
        return ok(None)
    return ok(advice)


async def _build_one(code: str, days: int) -> dict | None:
    navs = await nav_cache.get_nav_history(code, days=days, background_fetch=True)
    if not navs:
        return None

    with get_conn() as conn:
        name_row = conn.execute(
            "SELECT name FROM funds WHERE code = ?", (code,)
        ).fetchone()
        tx_rows = conn.execute(
            "SELECT date, type, nav, shares, amount, fee "
            "FROM transactions WHERE fund_code = ? ORDER BY date",
            (code,),
        ).fetchall()

    name = name_row["name"] if name_row else code

    profit_rate = None
    held_drawdown = None
    if tx_rows:
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
        if pos.shares > 1e-6:
            latest_nav = navs[0].nav if navs else 0.0
            _, profit_rate = profit.total_profit(pos, latest_nav)

            first_buy = next((t for t in txs if t.type == "buy"), None)
            if first_buy:
                held_navs = [n.nav for n in navs if n.date >= first_buy.date]
                if held_navs:
                    peak = max(held_navs)
                    held_drawdown = (latest_nav - peak) / peak if peak > 0 else None

    advice = advisor.build_advice(
        fund_code=code,
        fund_name=name,
        navs=navs,
        profit_rate=profit_rate,
        held_drawdown=held_drawdown,
    )
    return advice.model_dump()
