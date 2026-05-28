from __future__ import annotations

import logging
import time

from fastapi import APIRouter

from ..db import get_conn
from ..models.holding import HoldingsSummary, Position
from ..response import ok
from ..services import nav_cache, profit

router = APIRouter(prefix="/holdings", tags=["holdings"])
logger = logging.getLogger("fund.holdings")


@router.get("")
async def list_holdings() -> dict:
    """所有持仓汇总。"""
    t0 = time.time()
    logger.info("list_holdings: start request")
    summary, _ = await _get_holdings_summary()
    logger.info("list_holdings: finished request, elapsed: %.3fs", time.time() - t0)
    return ok(summary.model_dump())


async def _get_holdings_summary() -> tuple[HoldingsSummary, str]:
    """计算所有持仓汇总，并返回 (汇总数据, 当前最新的交易日)。"""
    t_start = time.time()
    logger.info("_get_holdings_summary: starting computation")
    with get_conn() as conn:
        codes = [
            r["code"]
            for r in conn.execute(
                "SELECT f.code FROM funds f "
                "JOIN (SELECT DISTINCT fund_code FROM transactions) t ON f.code = t.fund_code "
                "ORDER BY f.sort_order ASC, f.code ASC"
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
    global_trade_day = ""

    from collections import defaultdict
    with get_conn() as conn:
        all_tx_rows = conn.execute(
            "SELECT fund_code, date, type, nav, shares, amount, fee "
            "FROM transactions ORDER BY fund_code, date"
        ).fetchall()
        
    txs_by_fund = defaultdict(list)
    for r in all_tx_rows:
        txs_by_fund[r["fund_code"]].append(r)

    logger.info("_get_holdings_summary: DB query finished. Active funds: %d. Transaction rows: %d. Elapsed: %.3fs", len(codes), len(all_tx_rows), time.time() - t_start)

    # 1. 过滤有仓位的活跃持仓，并算好持仓份额
    active_codes = []
    positions_calc = {}
    for code in codes:
        tx_rows = txs_by_fund.get(code, [])
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
        active_codes.append(code)
        positions_calc[code] = (pos, txs)

    # 2. 并发拉取行情数据
    import asyncio
    t_quotes_start = time.time()
    logger.info("_get_holdings_summary: start concurrent fetch of quotes for active funds: %s", active_codes)
    quotes = await asyncio.gather(*(nav_cache.get_quote(code) for code in active_codes))
    quotes_map = dict(zip(active_codes, quotes))
    logger.info("_get_holdings_summary: concurrent fetch of quotes completed, elapsed: %.3fs", time.time() - t_quotes_start)

    # 3. 得到各基金交易日，并发拉取近两日净值
    trade_days_map = {}
    from datetime import datetime, timezone, timedelta
    beijing_tz = timezone(timedelta(hours=8))
    for code in active_codes:
        quote = quotes_map[code]
        if quote and quote.estimated_time:
            current_trade_day = quote.estimated_time[:10]
        else:
            current_trade_day = datetime.now(beijing_tz).strftime("%Y-%m-%d")
        
        trade_days_map[code] = current_trade_day
        if current_trade_day > global_trade_day:
            global_trade_day = current_trade_day

    t_navs_start = time.time()
    logger.info("_get_holdings_summary: start concurrent fetch of nav histories")
    navs_list = await asyncio.gather(*(
        nav_cache.get_nav_history(code, days=2, expected_date=trade_days_map[code])
        for code in active_codes
    ))
    navs_map = dict(zip(active_codes, navs_list))
    logger.info("_get_holdings_summary: concurrent fetch of nav histories completed, elapsed: %.3fs", time.time() - t_navs_start)

    # 4. 纯内存计算汇总及持仓列表组装
    for code in active_codes:
        pos, txs = positions_calc[code]
        quote = quotes_map[code]
        current_trade_day = trade_days_map[code]
        navs = navs_map[code]

        is_actual_published = False
        today_p = None
        today_r = None
        
        if navs and navs[0].date >= current_trade_day:
            # 历史净值表中已经包含了当天的真实净值 -> 已更新
            is_actual_published = True
            actual_latest_nav = navs[0].nav
            latest_date = navs[0].date
            yest_nav = navs[1].nav if len(navs) > 1 else None
            
            effective_nav = actual_latest_nav
            
            if yest_nav is not None:
                today_p, today_r = profit.actual_daily_profit(pos.shares, actual_latest_nav, yest_nav)
        else:
            # 真实净值还未公布，使用盘中估算净值 -> 未更新
            if navs:
                actual_latest_nav = navs[0].nav
                latest_date = navs[0].date
            else:
                actual_latest_nav = quote.nav if quote else 0.0
                latest_date = quote.nav_date if quote else ""
                
            if quote and quote.estimated_nav is not None:
                effective_nav = quote.estimated_nav
                today_p, today_r = profit.today_profit(pos.shares, actual_latest_nav, quote.estimated_nav)
            else:
                effective_nav = actual_latest_nav
        
        is_estimated = not is_actual_published
        
        # 市值和总收益基于 effective_nav 计算（已公布用真实，未公布用估算）
        market = profit.market_value(pos.shares, effective_nav)
        gain, gain_rate = profit.total_profit(pos, effective_nav)

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
                is_estimated=is_estimated,
                latest_nav=actual_latest_nav,
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
    
    yesterday_market = total_market - total_today
    today_rate = total_today / yesterday_market if yesterday_market > 1e-6 else 0.0

    if not positions:
        update_status = "estimated"
    else:
        num_est = sum(1 for p in positions if p.is_estimated)
        if num_est == 0:
            update_status = "updated"
        elif num_est == len(positions):
            update_status = "estimated"
        else:
            update_status = "updating"

    summary = HoldingsSummary(
        total_market_value=round(total_market, 4),
        total_cost=round(total_cost, 4),
        total_profit=round(total_profit_val, 4),
        total_profit_rate=round(rate, 6),
        today_profit=round(total_today, 4),
        today_profit_rate=round(today_rate, 6),
        is_estimated=any(p.is_estimated for p in positions) if positions else True,
        update_status=update_status,
        positions=positions,
        trade_date=global_trade_day,
    )
    if not global_trade_day:
        from datetime import datetime, timezone, timedelta
        global_trade_day = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        
    logger.info("_get_holdings_summary: summary calculation completed. Active positions: %d. Total elapsed: %.3fs", len(positions), time.time() - t_start)
    return summary, global_trade_day


@router.get("/history")
async def holdings_history(days: int = 30) -> dict:
    """计算最近 N 天的每日收益走势。"""
    t_start = time.time()
    logger.info("holdings_history: start request for days=%d", days)
    from collections import defaultdict

    with get_conn() as conn:
        codes = [
            r["fund_code"]
            for r in conn.execute("SELECT DISTINCT fund_code FROM transactions").fetchall()
        ]
        
        tx_rows = conn.execute(
            "SELECT fund_code, date, type, nav, shares, amount, fee FROM transactions WHERE nav > 0 ORDER BY date"
        ).fetchall()
        
        dates_result = conn.execute(
            "SELECT DISTINCT date FROM nav_history ORDER BY date DESC LIMIT ?", (days + 1,)
        ).fetchall()
        
    dates = sorted([r["date"] for r in dates_result])
    if len(dates) < 2:
        logger.info("holdings_history: too few dates, returning empty")
        return ok([])

    logger.info("holdings_history: loaded metadata. Active funds: %d. History dates: %d. Elapsed: %.3fs", len(codes), len(dates), time.time() - t_start)

    nav_map = {code: {} for code in codes}
    with get_conn() as conn:
        for code in codes:
            t_nav_start = time.time()
            rows = conn.execute(
                "SELECT date, nav FROM nav_history WHERE fund_code = ? AND date >= ?",
                (code, dates[0])
            ).fetchall()
            for r in rows:
                nav_map[code][r["date"]] = r["nav"]
            logger.info("holdings_history: loaded local nav for fund %s, records count: %d, elapsed: %.3fs", code, len(rows), time.time() - t_nav_start)

    txs_by_fund = defaultdict(list)
    for r in tx_rows:
        txs_by_fund[r["fund_code"]].append(r)

    first_tx_date = min((t["date"] for t in tx_rows), default="9999-12-31")

    history = []
    for i in range(1, len(dates)):
        today = dates[i]
        
        # 只显示首笔交易生效之后的走势
        if today < first_tx_date:
            continue
            
        yesterday = dates[i-1]
        
        daily_profit = 0.0
        cumulative_profit = 0.0
        for code in codes:
            # 取出当日及之前的交易记录计算成本和份额
            txs_up_to_today = [t for t in txs_by_fund[code] if t["date"] <= today]
            if not txs_up_to_today:
                continue
                
            txs = [profit.TxRow(
                date=t["date"], type=t["type"], nav=t["nav"],
                shares=t["shares"], amount=t["amount"], fee=t["fee"]
            ) for t in txs_up_to_today]
            
            pos = profit.compute_position(txs)
            nav_today = nav_map[code].get(today)
            
            if pos.shares > 1e-6 and nav_today:
                market = profit.market_value(pos.shares, nav_today)
                cumulative_profit += (market - pos.cost_amount)
                
            # 计算当日收益：拿当日初份额 * (今日净值 - 昨日净值)
            shares_start_of_day = sum(
                (t["shares"] if t["type"] == "buy" else -t["shares"])
                for t in txs_by_fund[code]
                if t["date"] < today
            )
            nav_yest = nav_map[code].get(yesterday)
            
            if shares_start_of_day > 1e-6 and nav_today and nav_yest:
                daily_profit += shares_start_of_day * (nav_today - nav_yest)
                
        history.append({
            "date": today,
            "profit": round(daily_profit, 2),
            "cumulative_profit": round(cumulative_profit, 2)
        })

    logger.info("holdings_history: history generation completed, history points: %d, total elapsed: %.3fs", len(history), time.time() - t_start)
    return ok(history)
