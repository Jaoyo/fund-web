from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Fund(BaseModel):
    code: str = Field(..., description="基金代码，6 位")
    name: str
    type: Optional[str] = None
    updated_at: Optional[str] = None


class NavRecord(BaseModel):
    date: str
    nav: float
    accumulated_nav: Optional[float] = None
    growth_rate: Optional[float] = None


class Quote(BaseModel):
    """实时估值。盘后可能没有 estimated_nav。"""

    code: str
    name: str
    nav_date: str
    nav: float
    estimated_nav: Optional[float] = None
    estimated_growth: Optional[float] = None
    estimated_time: Optional[str] = None


class FundDetail(BaseModel):
    fund: Fund
    quote: Optional[Quote] = None


class FundAddRequest(BaseModel):
    code: str = Field(..., description="基金代码，6 位")


class FundSortRequest(BaseModel):
    codes: list[str] = Field(..., description="排好序的基金代码列表")
