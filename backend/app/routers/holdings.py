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

    from collections import defaultdict
    with get_conn() as conn:
        all_tx_rows = conn.execute(
            "SELECT fund_code, date, type, nav, shares, amount, fee "
            "FROM transactions ORDER BY fund_code, date"
        ).fetchall()
        
    txs_by_fund = defaultdict(list)
    for r in all_tx_rows:
        txs_by_fund[r["fund_code"]].append(r)

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

        quote = await nav_cache.get_quote(code)
        latest_nav = quote.nav if quote else 0.0
        latest_date = quote.nav_date if quote else ""

        market = profit.market_value(pos.shares, latest_nav)
        gain, gain_rate = profit.total_profit(pos, latest_nav)
        
        is_estimated = True
        is_actual_published = False
        if quote and quote.nav_date and quote.estimated_time:
            if quote.nav_date == quote.estimated_time[:10]:
                is_actual_published = True

        if quote and quote.estimated_nav is not None and not is_actual_published:
            today_p, today_r = profit.today_profit(
                pos.shares, latest_nav, quote.estimated_nav
            )
        else:
            is_estimated = False
            navs = await nav_cache.get_nav_history(code, days=2)
            if quote and len(navs) >= 1:
                # 确定昨日净值：如果缓存首条是今天，则昨收为第二条；否则首条即为昨收
                if navs[0].date == quote.nav_date:
                    yest_nav = navs[1].nav if len(navs) > 1 else None
                else:
                    yest_nav = navs[0].nav

                if yest_nav:
                    today_p, today_r = profit.actual_daily_profit(
                        pos.shares, quote.nav, yest_nav
                    )
                else:
                    today_p, today_r = None, None
            else:
                today_p, today_r = None, None

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
    )
    return ok(summary.model_dump())


@router.get("/history")
async def holdings_history(days: int = 30) -> dict:
    """计算最近 N 天的每日收益走势。"""
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
        return ok([])

    nav_map = {code: {} for code in codes}
    with get_conn() as conn:
        for code in codes:
            rows = conn.execute(
                "SELECT date, nav FROM nav_history WHERE fund_code = ? AND date >= ?",
                (code, dates[0])
            ).fetchall()
            for r in rows:
                nav_map[code][r["date"]] = r["nav"]

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
            "profit": round(daily_profit, 4),
            "cumulative_profit": round(cumulative_profit, 4)
        })
        
    return ok(history)
