from __future__ import annotations

from fastapi import APIRouter

from ..db import get_conn
from ..models.fund import FundDetail, FundSortRequest
from ..response import BizError, ok
from ..services import eastmoney, nav_cache

router = APIRouter(prefix="/funds", tags=["funds"])

@router.put("/sort")
async def update_sort(payload: FundSortRequest) -> dict:
    """更新基金的自定义排序顺序。"""
    with get_conn() as conn:
        # 先把所有的基金排序放到最后，防止已清仓的基金（没在 payload 里）sort_order 为 0 跑到最前面
        conn.execute("UPDATE funds SET sort_order = 9999")
        for i, code in enumerate(payload.codes):
            conn.execute(
                "UPDATE funds SET sort_order = ? WHERE code = ?",
                (i, code)
            )
    return ok({"sorted": len(payload.codes)})


@router.get("/{code}")
async def get_fund(code: str) -> dict:
    """基金基本信息 + 实时估值（盘后无估值则只返回净值）。"""
    try:
        quote = await nav_cache.get_quote(code)
        info = await eastmoney.fetch_fund_info(code, quote=quote)
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
