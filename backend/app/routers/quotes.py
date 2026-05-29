from __future__ import annotations

from fastapi import APIRouter

from ..response import ok
from ..services import nav_cache

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/{code}")
async def get_quote(code: str) -> dict:
    """实时估值（60s 缓存）。盘后/节假日返回 quote=null。"""
    quote = await nav_cache.get_quote(code)
    return ok(quote.model_dump() if quote else None)
