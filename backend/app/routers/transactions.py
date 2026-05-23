from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from ..db import get_conn
from ..models.holding import Transaction, TransactionIn
from ..response import BizError, ok
from ..services import eastmoney

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("")
async def create_transaction(payload: TransactionIn) -> dict:
    """录入交易。

    幂等：如果带 client_id 且数据库已有同 client_id 的记录，直接返回旧记录、不重复插入。
    amount 和 shares 至少给一个，缺的那个用 nav 反推（暂不考虑卖出费用对 amount 的影响）。
    """
    if payload.amount is None and payload.shares is None:
        raise BizError(4001, "amount 和 shares 至少提供一个")

    shares = payload.shares
    amount = payload.amount
    if shares is None:
        shares = (amount - payload.fee) / payload.nav if payload.type == "buy" else amount / payload.nav
    if amount is None:
        amount = shares * payload.nav

    if payload.client_id:
        with get_conn() as conn:
            existing = conn.execute(
                "SELECT * FROM transactions WHERE client_id = ?",
                (payload.client_id,),
            ).fetchone()
        if existing:
            return ok(_row_to_dict(existing), message="idempotent hit")

    try:
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
                payload.nav,
                shares,
                amount,
                payload.fee,
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


def _row_to_dict(row) -> dict:
    return dict(row) if row else {}
