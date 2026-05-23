"""净值缓存策略。

- 实时估值：内存缓存 60 秒（盘中频繁调用，避免打爆东财）
- 历史净值：写到 SQLite，按日期主键去重，调用方先查 DB，缺数据再拉
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from ..config import QUOTE_TTL_SECONDS
from ..db import get_conn
from ..models.fund import NavRecord, Quote
from . import eastmoney

_quote_cache: dict[str, tuple[float, Quote | None]] = {}


async def get_quote(code: str) -> Quote | None:
    now = time.time()
    cached = _quote_cache.get(code)
    if cached and now - cached[0] < QUOTE_TTL_SECONDS:
        return cached[1]

    quote = await eastmoney.fetch_quote(code)
    _quote_cache[code] = (now, quote)

    if quote:
        _upsert_fund(code, quote.name)
        if quote.nav and quote.nav_date:
            _upsert_nav(code, quote.nav_date, quote.nav, None, None)
    return quote


async def get_nav_history(code: str, days: int = 60) -> list[NavRecord]:
    """优先从 DB 读，不够就拉东财补齐。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date, nav, accumulated_nav, growth_rate "
            "FROM nav_history WHERE fund_code = ? "
            "ORDER BY date DESC LIMIT ?",
            (code, days),
        ).fetchall()

    if len(rows) >= days:
        return [
            NavRecord(
                date=r["date"],
                nav=r["nav"],
                accumulated_nav=r["accumulated_nav"],
                growth_rate=r["growth_rate"],
            )
            for r in rows
        ]

    fresh = await eastmoney.fetch_nav_history(code, page_size=max(days, 60))
    _bulk_upsert_nav(code, fresh)
    return fresh[:days]


async def refresh_all() -> int:
    """全量刷新所有已持有基金的最新净值。返回刷新基金数。"""
    with get_conn() as conn:
        codes = [
            r["fund_code"]
            for r in conn.execute(
                "SELECT DISTINCT fund_code FROM transactions"
            ).fetchall()
        ]

    for code in codes:
        try:
            records = await eastmoney.fetch_nav_history(code, page_size=30)
            _bulk_upsert_nav(code, records)
        except Exception:
            continue
    return len(codes)


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
