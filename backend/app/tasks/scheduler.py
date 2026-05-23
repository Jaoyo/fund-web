"""APScheduler 定时任务。

每个交易日 21:00 拉一次净值（净值大概 20:00 出，留 1 小时余量）。
"""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import NAV_REFRESH_HOUR, NAV_REFRESH_MINUTE
from ..services import nav_cache

log = logging.getLogger("fund.scheduler")

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    if _scheduler:
        return
    _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    _scheduler.add_job(
        _refresh_nav_job,
        CronTrigger(
            day_of_week="mon-fri",
            hour=NAV_REFRESH_HOUR,
            minute=NAV_REFRESH_MINUTE,
        ),
        id="refresh_nav",
        replace_existing=True,
    )
    _scheduler.start()
    log.info("scheduler started: refresh_nav at %d:%02d (Mon-Fri)",
             NAV_REFRESH_HOUR, NAV_REFRESH_MINUTE)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


async def _refresh_nav_job() -> None:
    try:
        n = await nav_cache.refresh_all()
        log.info("nav refresh done: %d funds", n)
    except Exception as e:
        log.exception("nav refresh failed: %s", e)


async def trigger_refresh_now() -> int:
    """手动触发一次刷新（供 /api/v1/quotes/refresh 这类后续接口调用）。"""
    return await nav_cache.refresh_all()
