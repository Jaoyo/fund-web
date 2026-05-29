from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from ..db import get_conn
from ..models.fund import Fund
from ..models.holding import Transaction, TransactionIn
from ..response import BizError, ok
from ..services import eastmoney, nav_cache

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("")
async def create_transaction(payload: TransactionIn) -> dict:
    """录入交易。

    幂等：如果带 client_id 且数据库已有同 client_id 的记录，直接返回旧记录、不重复插入。
    amount 和 shares 至少给一个，缺的那个用 nav 反推（暂不考虑卖出费用对 amount 的影响）。
    """
    if payload.client_id:
        with get_conn() as conn:
            existing = conn.execute(
                "SELECT * FROM transactions WHERE client_id = ?",
                (payload.client_id,),
            ).fetchone()
        if existing:
            return ok(_row_to_dict(existing), message="idempotent hit")

    custom_name = payload.fund_name

    if payload.type == "import":
        if payload.amount is None or payload.profit is None:
            raise BizError(4002, "导入持仓必须提供当前市值(amount)和累计收益(profit)")

        # 获取最新的实时估值或历史净值
        latest_nav = 0.0
        quote = await nav_cache.get_quote(payload.fund_code)
        if quote and quote.nav > 0:
            latest_nav = quote.nav
        else:
            nav_history = await nav_cache.get_nav_history(payload.fund_code, days=10)
            if nav_history:
                latest_nav = nav_history[0].nav

        if latest_nav <= 0:
            raise BizError(4042, f"未获取到基金 {payload.fund_code} 的最新净值，无法导入旧持仓")

        market_value = round(payload.amount, 2)
        profit_val = round(payload.profit, 2)
        cost_amount = round(market_value - profit_val, 2)
        shares = round(market_value / latest_nav, 2)
        nav = round(cost_amount / shares, 4) if shares > 0 else 0.0
        amount = round(cost_amount, 2)

        # 保留 type = "import" 入库，收益计算时可区分：import 当天即生效，buy 需要 T+1
        payload.shares = shares  # 避免后面 not payload.shares 逻辑再次除以 nav 造成精度损失
        if not payload.note:
            payload.note = f"初始化导入(市值:{market_value:.2f},收益:{profit_val:.2f})"
    else:
        if payload.type == "buy" and payload.amount is None:
            raise BizError(4001, "买入时必须提供金额")
        if payload.type == "sell" and payload.shares is None:
            raise BizError(4001, "卖出时必须提供份额")

        shares = round(payload.shares, 2) if payload.shares is not None else 0.0
        amount = round(payload.amount, 2) if payload.amount is not None else 0.0
        nav = payload.nav

        # 如果没有提供确切净值，尝试去缓存查，或者标记为待确认
        if nav is None or nav <= 0:
            nav_history = await nav_cache.get_nav_history(payload.fund_code, days=30)
            nav_record = next((r for r in nav_history if r.date == payload.date), None)
            if nav_record and nav_record.nav > 0:
                nav = nav_record.nav
            else:
                nav = 0.0  # 0.0 标识待确认

    fee = round(payload.fee, 2)
    if nav > 0:
        nav = round(nav, 4)
        if payload.type in ("buy", "import") and not payload.shares:
            shares = round((amount - fee) / nav, 2)
        elif payload.type == "sell" and not payload.amount:
            amount = round(shares * nav, 2)
    else:
        # 待确认订单（import 不会走到这里，因为前面已算好 nav）
        if payload.type in ("buy", "import"):
            shares = 0.0
        else:
            amount = 0.0

    try:
        if custom_name:
            info = Fund(code=payload.fund_code, name=custom_name)
        else:
            info = await eastmoney.fetch_fund_info(payload.fund_code)
    except BizError:
        raise
    except Exception as e:
        raise BizError(4040, f"基金 {payload.fund_code} 校验失败: {e}")

    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO funds(code, name, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(code) DO UPDATE SET name=excluded.name, updated_at=excluded.updated_at",
            (payload.fund_code, info.name, now),
        )
        cur = conn.execute(
            "INSERT INTO transactions"
            "(client_id, fund_code, date, type, nav, shares, amount, fee, note, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                payload.client_id,
                payload.fund_code,
                payload.date,
                payload.type,
                nav,
                shares,
                amount,
                fee,
                payload.note,
                now,
            ),
        )
        new_id = cur.lastrowid
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (new_id,)
        ).fetchone()

    return ok(_row_to_dict(row))


@router.get("")
async def list_transactions(fund_code: str | None = None) -> dict:
    sql = "SELECT * FROM transactions"
    params: tuple = ()
    if fund_code:
        sql += " WHERE fund_code = ?"
        params = (fund_code,)
    sql += " ORDER BY date DESC, id DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return ok([_row_to_dict(r) for r in rows])


@router.delete("/{tx_id}")
async def delete_transaction(tx_id: int) -> dict:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        if cur.rowcount == 0:
            raise BizError(4041, f"交易 {tx_id} 不存在")
    return ok({"deleted": tx_id})


@router.post("/sync_pending")
async def sync_pending() -> dict:
    """手动触发待确认订单的同步补全。"""
    count = await nav_cache.sync_pending_transactions()
    return ok({"synced_count": count})

def _row_to_dict(row) -> dict:
    return dict(row) if row else {}
