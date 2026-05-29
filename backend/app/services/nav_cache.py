"""净值缓存策略。

- 实时估值：内存缓存 60 秒（盘中频繁调用，避免打爆东财）
- 历史净值：写到 SQLite，按日期主键去重，调用方先查 DB，缺数据再拉
- 新鲜度保障：缓存最新日期 < 昨天时，增量拉最近数据补齐
"""
from __future__ import annotations

import time
import math
import asyncio
import httpx
from datetime import datetime, timedelta, timezone

from ..config import QUOTE_TTL_SECONDS
from ..db import get_conn
from ..models.fund import NavRecord, Quote
from . import eastmoney

# 历史净值刷新节流：记录每只基金上次从东财拉取的时间戳，避免短时间内重复请求
_nav_refresh_ts: dict[str, float] = {}
_NAV_REFRESH_INTERVAL = 3600  # 同一基金至少间隔 1 小时才再次请求东财

# 结构为 {code: (expires_at, quote)}。其中 expires_at 是物理截止过期时间戳
_quote_cache: dict[str, tuple[float, Quote | None]] = {}
_QUOTE_FAILURE_TTL_SECONDS = 15

# 记录已知的每只基金在东财拥有的全部历史净值天数（避免对新发行基金反复拉取）
_fund_total_count: dict[str, int] = {}

# 增量更新时拉取的条数（覆盖最近几个交易日即可）
_INCREMENTAL_FETCH_SIZE = 10


def _rows_to_nav_records(rows) -> list[NavRecord]:
    return [
        NavRecord(
            date=r["date"],
            nav=r["nav"],
            accumulated_nav=r["accumulated_nav"],
            growth_rate=r["growth_rate"],
        )
        for r in rows
    ]


def _trading_days_needed(start_date: str, min_days: int = 30) -> int:
    """估算从 start_date 到今天需要覆盖的交易日数量。"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
    except ValueError:
        return min_days

    beijing_today = datetime.now(timezone(timedelta(hours=8))).date()
    if start > beijing_today:
        return min_days

    calendar_days = (beijing_today - start).days + 1
    # 基金净值大致每周 5 个交易日，留 20% 余量覆盖假期和接口分页截断。
    trading_days = math.ceil(calendar_days * 5 / 7 * 1.2)
    return max(min_days, trading_days)


import logging

logger = logging.getLogger("fund.nav_cache")


async def get_quote(code: str) -> Quote | None:
    now = time.time()
    cached = _quote_cache.get(code)
    if cached and now < cached[0]:
        return cached[1]

    try:
        quote = await eastmoney.fetch_quote(code)
        _quote_cache[code] = (now + QUOTE_TTL_SECONDS, quote)
        if quote:
            _upsert_fund(code, quote.name)
            if quote.nav and quote.nav_date:
                _upsert_nav(code, quote.nav_date, quote.nav, None, None)
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error("get_quote: network error fetching quote for fund %s, error: %s", code, e)
        quote = None
        # 缓存 15 秒空值以避免瞬时请求反复穿透重试
        _quote_cache[code] = (now + _QUOTE_FAILURE_TTL_SECONDS, None)
    return quote


def _is_cache_fresh(rows, expected_date: str | None = None) -> bool:
    """判断缓存是否足够新鲜。"""
    if not rows:
        return False
    latest_date = rows[0]["date"]  # 已按 date DESC 排序
    
    beijing_now = datetime.now(timezone(timedelta(hours=8)))
    today_str = beijing_now.strftime("%Y-%m-%d")

    if expected_date:
        if expected_date == today_str:
            if beijing_now.hour >= 20:
                # 到了交易日当晚 20 点以后，必须拿到当天的真实净值才算新鲜
                return latest_date >= expected_date
            # 还没到晚上 20 点，放行到兜底逻辑
        else:
            # 估值停留在过去（比如周末、节假日，或者是次日早盘前）
            # 此时 expected_date 的净值早已公布，本地必须有
            return latest_date >= expected_date

    # 兜底逻辑：用北京时间判断，只要有昨天的数据就算新鲜
    yesterday = (beijing_now - timedelta(days=1)).strftime("%Y-%m-%d")
    return latest_date >= yesterday


async def get_nav_history(
    code: str, 
    days: int = 60, 
    expected_date: str | None = None,
    background_fetch: bool = False
) -> list[NavRecord]:
    """优先从 DB 读。数量不够则全量拉；数量够但不新鲜则增量补齐。支持后台静默补齐。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date, nav, accumulated_nav, growth_rate "
            "FROM nav_history WHERE fund_code = ? "
            "ORDER BY date DESC LIMIT ?",
            (code, days),
        ).fetchall()

    has_enough = len(rows) >= days
    if not has_enough:
        known_total = _fund_total_count.get(code)
        if known_total is not None and len(rows) >= known_total:
            has_enough = True

    fresh = _is_cache_fresh(rows, expected_date)

    # 快速路径：数据足够且新鲜，直接返回
    if has_enough and fresh:
        return [
            NavRecord(
                date=r["date"],
                nav=r["nav"],
                accumulated_nav=r["accumulated_nav"],
                growth_rate=r["growth_rate"],
            )
            for r in rows
        ]

    # 检查内存节流：只有当前缓存已经满足数量要求时才短路。
    now = time.time()
    last_refresh = _nav_refresh_ts.get(code, 0)
    if has_enough and now - last_refresh < _NAV_REFRESH_INTERVAL:
        return _rows_to_nav_records(rows)

    # 如果允许后台拉取且本地至少有一条历史数据，则直接发起后台任务并快速返回
    if background_fetch and len(rows) > 0:
        if now - last_refresh >= _NAV_REFRESH_INTERVAL:
            _nav_refresh_ts[code] = now
            
            async def _bg_fetch_and_save():
                try:
                    if has_enough and not fresh:
                        records, total_count = await eastmoney.fetch_nav_history(code, page_size=_INCREMENTAL_FETCH_SIZE)
                    else:
                        records, total_count = await eastmoney.fetch_nav_history(code, page_size=max(days, 60))
                    
                    _fund_total_count[code] = total_count
                    _bulk_upsert_nav(code, records)
                except Exception as ex:
                    logger.error("bg_fetch: failed for fund %s, error: %s", code, ex)
                    
            asyncio.create_task(_bg_fetch_and_save())
            
        return _rows_to_nav_records(rows)

    # 决定拉取策略
    try:
        if has_enough and not fresh:
            # 数据量够但不新鲜 → 只增量拉最近几条补齐
            records, total_count = await eastmoney.fetch_nav_history(code, page_size=_INCREMENTAL_FETCH_SIZE)
        else:
            # 数据量不够 → 全量拉取
            records, total_count = await eastmoney.fetch_nav_history(code, page_size=max(days, 60))

        _fund_total_count[code] = total_count
        _bulk_upsert_nav(code, records)
        _nav_refresh_ts[code] = now
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error("get_nav_history: network error fetching nav history for fund %s, fallback to DB: %s", code, e)

    # 从 DB 重新读取合并后的完整数据
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date, nav, accumulated_nav, growth_rate "
            "FROM nav_history WHERE fund_code = ? "
            "ORDER BY date DESC LIMIT ?",
            (code, days),
        ).fetchall()

    return _rows_to_nav_records(rows)


async def refresh_all() -> tuple[int, int]:
    """全量刷新所有已持有基金的最新净值。返回 (刷新基金数, 成功同步的订单数)。"""
    with get_conn() as conn:
        codes = [
            r["fund_code"]
            for r in conn.execute(
                "SELECT DISTINCT fund_code FROM transactions"
            ).fetchall()
        ]

    for code in codes:
        try:
            # 只拉最新 1 条净值（Quote 接口盘后 dwjz 不更新当天，必须用 NAV 接口）
            records, total_count = await eastmoney.fetch_nav_history(code, page_size=1)
            _fund_total_count[code] = total_count
            _bulk_upsert_nav(code, records)
        except Exception:
            continue

    # 刷新净值后，尝试同步所有待确认订单
    sync_count = await sync_pending_transactions()
    return len(codes), sync_count


async def sync_pending_transactions() -> int:
    """扫描所有未知价（待确认）订单，如果已有净值则补全份额和金额。返回成功同步的订单数。"""
    with get_conn() as conn:
        pending_txs = conn.execute(
            "SELECT id, fund_code, date, type, shares, amount, fee, settlement_days FROM transactions WHERE nav = 0.0"
        ).fetchall()

    if not pending_txs:
        return 0

    from collections import defaultdict
    txs_by_fund = defaultdict(list)
    for tx in pending_txs:
        txs_by_fund[tx["fund_code"]].append(tx)

    sync_count = 0
    for code, txs in txs_by_fund.items():
        # 按 fund_code 统一获取净值历史，覆盖最早待确认交易日期，避免历史交易永久待确认。
        earliest_date = min(tx["date"] for tx in txs)
        nav_history = await get_nav_history(code, days=_trading_days_needed(earliest_date))

        for tx in txs:
            nav_asc = list(reversed(nav_history))
            idx = next((i for i, r in enumerate(nav_asc) if r.date >= tx["date"]), None)
            
            nav_record = None
            if idx is not None:
                settlement_days = tx["settlement_days"]
                target_idx = idx + (settlement_days - 1)
                if target_idx < len(nav_asc):
                    nav_record = nav_asc[target_idx]

            if nav_record and nav_record.nav > 0:
                nav = round(nav_record.nav, 4)
                if tx["type"] in ("buy", "import"):
                    # 买入待确认：已知 amount，求 shares
                    amount = round(tx["amount"], 2)
                    shares = round((amount - tx["fee"]) / nav, 2)
                else:
                    # 卖出待确认：已知 shares，求 amount
                    shares = round(tx["shares"], 2)
                    amount = round(shares * nav, 2)

                with get_conn() as conn:
                    conn.execute(
                        "UPDATE transactions SET nav = ?, shares = ?, amount = ? WHERE id = ?",
                        (nav, shares, amount, tx["id"]),
                    )
                sync_count += 1

    return sync_count


def _upsert_fund(code: str, name: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO funds(code, name, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(code) DO UPDATE SET name=excluded.name, updated_at=excluded.updated_at",
            (code, name, now),
        )


def _upsert_nav(code: str, date: str, nav: float, acc: float | None, growth: float | None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO nav_history(fund_code, date, nav, accumulated_nav, growth_rate) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(fund_code, date) DO UPDATE SET "
            "nav=excluded.nav, accumulated_nav=excluded.accumulated_nav, growth_rate=excluded.growth_rate",
            (code, date, nav, acc, growth),
        )


def _bulk_upsert_nav(code: str, records: list[NavRecord]) -> None:
    if not records:
        return
    rows = [
        (code, r.date, r.nav, r.accumulated_nav, r.growth_rate) for r in records
    ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO nav_history(fund_code, date, nav, accumulated_nav, growth_rate) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(fund_code, date) DO UPDATE SET "
            "nav=excluded.nav, accumulated_nav=excluded.accumulated_nav, growth_rate=excluded.growth_rate",
            rows,
        )
