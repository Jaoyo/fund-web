from __future__ import annotations

import logging
import time

from fastapi import APIRouter

from ..response import ok
from ..services import nav_cache

router = APIRouter(prefix="/quotes", tags=["quotes"])
logger = logging.getLogger("fund.quotes")


@router.get("/{code}")
async def get_quote(code: str) -> dict:
    """实时估值（60s 缓存）。盘后/节假日返回 quote=null。"""
    t0 = time.time()
    logger.info("get_quote (route): start request code=%s", code)
    quote = await nav_cache.get_quote(code)
    logger.info("get_quote (route): completed for %s, elapsed: %.3fs", code, time.time() - t0)
    return ok(quote.model_dump() if quote else None)
