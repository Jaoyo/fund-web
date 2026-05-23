from __future__ import annotations

from fastapi import APIRouter

from ..models.fund import FundDetail
from ..response import BizError, ok
from ..services import eastmoney, nav_cache

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("/{code}")
async def get_fund(code: str) -> dict:
    """基金基本信息 + 实时估值（盘后无估值则只返回净值）。"""
    try:
        info = await eastmoney.fetch_fund_info(code)
        quote = await nav_cache.get_quote(code)
    except BizError:
        raise
    except Exception as e:
        raise BizError(5002, f"获取基金信息失败: {e}")

    return ok(FundDetail(fund=info, quote=quote).model_dump())


@router.get("/{code}/nav")
async def get_nav(code: str, days: int = 60) -> dict:
    """历史净值。默认 60 个交易日，advisor 用最多 750 天（约 3 年）。"""
    days = max(1, min(days, 1500))
    records = await nav_cache.get_nav_history(code, days=days)
    return ok([r.model_dump() for r in records])
