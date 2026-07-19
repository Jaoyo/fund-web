from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from ..db import get_conn
from ..models.fund import Fund
from ..models.holding import Transaction, TransactionIn
from ..response import BizError, ok
from ..services import eastmoney, nav_cache

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = logging.getLogger("fund.transactions")


@router.post("")
async def create_transaction(payload: TransactionIn) -> dict:
    """录入交易。

    幂等：如果带 client_id 且数据库已有同 client_id 的记录，直接返回旧记录、不重复插入。
    amount 和 shares 至少给一个，缺隔那个用 nav 反推（暂不考虑卖出费用对 amount 的影响）。
    """
    if payload.client_id:
        with get_conn() as conn:
            existing = conn.execute(
                "SELECT * FROM transactions WHERE client_id = ?",
                (payload.client_id,),
            ).fetchone()
        if existing:
            logger.info("触发幂等命中，跳过交易录入 - client_id: %s", payload.client_id)
            return ok(_row_to_dict(existing), message="idempotent hit")

    custom_name = payload.fund_name

    logger.info("收到交易录入请求 - 基金代码: %s, 交易日期: %s, 交易类型: %s", payload.fund_code, payload.date, payload.type)

    if payload.type == "import":
        if payload.amount is None or payload.profit is None:
            raise BizError(4002, "导入持仓必须提供当前市值(amount)和累计收益(profit)")

        logger.info("开始导入历史持仓计算 - 输入当前市值: %s, 累计收益: %s", payload.amount, payload.profit)

        # 获取最新的实时估值或历史净值
        latest_nav = 0.0
        quote = await nav_cache.get_quote(payload.fund_code)
        if quote and quote.nav > 0:
            latest_nav = quote.nav
            logger.info("获取最新参考净值: %s (来源: 实时估值, 净值日期: %s)", latest_nav, quote.nav_date)
        else:
            nav_history = await nav_cache.get_nav_history(payload.fund_code, days=10)
            if nav_history:
                latest_nav = nav_history[0].nav
                logger.info("获取最新参考净值: %s (来源: 历史净值表, 净值日期: %s)", latest_nav, nav_history[0].date)

        if latest_nav <= 0:
            raise BizError(4042, f"未获取到基金 {payload.fund_code} 的最新净值，无法导入旧持仓")

        market_value = round(payload.amount, 2)
        profit_val = round(payload.profit, 2)
        cost_amount = round(market_value - profit_val, 2)
        shares = round(market_value / latest_nav, 2)
        nav = round(cost_amount / shares, 4) if shares > 0 else 0.0
        amount = round(cost_amount, 2)

        logger.info("持仓导入计算过程:\n"
                    "  - 历史总成本 = 市值 (%s) - 累计收益 (%s) = %s 元\n"
                    "  - 计算所得份额 = 市值 (%s) / 最新净值 (%s) = %s 份\n"
                    "  - 换算成交均价 (成本价) = 历史总成本 (%s) / 持有份额 (%s) = %s 元",
                    market_value, profit_val, cost_amount,
                    market_value, latest_nav, shares,
                    cost_amount, shares, nav)

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
            logger.info("未提供成交净值，尝试从缓存/历史匹配交易日 %s 的净值 (交收天数: %s)...", payload.date, payload.settlement_days)
            nav_history = await nav_cache.get_nav_history(payload.fund_code, days=30)
            nav_asc = list(reversed(nav_history))
            idx = next((i for i, r in enumerate(nav_asc) if r.date >= payload.date), None)
            
            nav_record = None
            if idx is not None:
                target_idx = idx + (payload.settlement_days - 1)
                if target_idx < len(nav_asc):
                    nav_record = nav_asc[target_idx]
                    logger.info("定位到交易日索引: %s, 目标确认净值索引: %s", idx, target_idx)
                    
            if nav_record and nav_record.nav > 0:
                nav = nav_record.nav
                logger.info("成功匹配到确认净值: %s (日期: %s)", nav, nav_record.date)
            else:
                nav = 0.0  # 0.0 标识待确认
                logger.info("未匹配到已公布净值，交易将作为「待确认」记录入库")

    fee = round(payload.fee, 2)
    if nav > 0:
        nav = round(nav, 4)
        if payload.type in ("buy", "import") and not payload.shares:
            shares = round((amount - fee) / nav, 2)
            logger.info("计算完成 - 申购份额: (交易金额: %s - 手续费: %s) / 成交净值: %s = %s 份", amount, fee, nav, shares)
        elif payload.type == "sell" and not payload.amount:
            amount = round(shares * nav, 2)
            logger.info("计算完成 - 赎回金额: 确认份额: %s * 成交净值: %s = %s 元", shares, nav, amount)
    else:
        # 待确认订单（import 不会走到这里，因为前面已算好 nav）
        if payload.type in ("buy", "import"):
            shares = 0.0
            logger.info("买入待确认订单 - 暂设份额为 0.0，等待后续同步确认")
        else:
            amount = 0.0
            logger.info("卖出待确认订单 - 暂设金额为 0.0，等待后续同步确认")

    try:
        if custom_name:
            info = Fund(code=payload.fund_code, name=custom_name)
        else:
            info = await eastmoney.fetch_fund_info(payload.fund_code)
    except BizError:
        raise
    except Exception as e:
        raise BizError(4040, f"基金 {payload.fund_code} 校验失败: {e}")

    if not payload.note or not payload.note.strip():
        payload.note = info.name

    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO funds(code, name, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(code) DO UPDATE SET name=excluded.name, updated_at=excluded.updated_at",
            (payload.fund_code, info.name, now),
        )
        cur = conn.execute(
            "INSERT INTO transactions"
            "(client_id, fund_code, date, type, nav, shares, amount, fee, settlement_days, note, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                payload.client_id,
                payload.fund_code,
                payload.date,
                payload.type,
                nav,
                shares,
                amount,
                fee,
                payload.settlement_days,
                payload.note,
                now,
            ),
        )
        new_id = cur.lastrowid
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (new_id,)
        ).fetchone()

    logger.info("交易录入保存成功 - 生成记录 ID: %s, 基金名称: %s", new_id, info.name)
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
    logger.info("收到交易删除请求 - 记录 ID: %s", tx_id)
    with get_conn() as conn:
        tx_row = conn.execute("SELECT fund_code, date, type, amount, shares FROM transactions WHERE id = ?", (tx_id,)).fetchone()
        if not tx_row:
            logger.warning("删除失败 - 交易记录不存在 - ID: %s", tx_id)
            raise BizError(4041, f"交易 {tx_id} 不存在")
            
        conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        logger.info("交易删除成功 - ID: %s, 基金代码: %s, 日期: %s, 类型: %s, 金额: %s, 份额: %s",
                    tx_id, tx_row["fund_code"], tx_row["date"], tx_row["type"], tx_row["amount"], tx_row["shares"])
    return ok({"deleted": tx_id})


@router.post("/sync_pending")
async def sync_pending() -> dict:
    """手动触发待确认订单的同步补全。"""
    count = await nav_cache.sync_pending_transactions()
    return ok({"synced_count": count})

def _row_to_dict(row) -> dict:
    return dict(row) if row else {}
