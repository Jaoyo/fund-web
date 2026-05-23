from __future__ import annotations

from fastapi import APIRouter

from ..db import get_conn
from ..response import ok
from ..services import advisor, nav_cache, profit

router = APIRouter(prefix="/advice", tags=["advice"])


@router.get("")
async def list_advice() -> dict:
    """所有持仓基金的建议汇总。"""
    with get_conn() as conn:
        codes = [
            r["fund_code"]
            for r in conn.execute(
                "SELECT DISTINCT fund_code FROM transactions"
            ).fetchall()
        ]

    results = []
    for code in codes:
        advice = await _build_one(code)
        if advice:
            results.append(advice)
    return ok(results)


@router.get("/{code}")
async def get_advice(code: str) -> dict:
    """单基金详细指标。即使没持仓也能查（用于决定要不要建仓）。"""
    advice = await _build_one(code)
    if advice is None:
        return ok(None)
    return ok(advice)


async def _build_one(code: str) -> dict | None:
    navs = await nav_cache.get_nav_history(code, days=750)
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
