from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    """录入交易。amount 和 shares 至少给一个，缺的那个由 nav 算出。"""

    client_id: Optional[str] = Field(None, description="幂等 ID，可选")
    fund_code: str
    date: str = Field(..., description="YYYY-MM-DD")
    type: Literal["buy", "sell"]
    nav: float = Field(..., gt=0, description="成交净值")
    shares: Optional[float] = Field(None, gt=0)
    amount: Optional[float] = Field(None, gt=0)
    fee: float = Field(0, ge=0)
    note: Optional[str] = None


class Transaction(BaseModel):
    id: int
    client_id: Optional[str]
    fund_code: str
    date: str
    type: Literal["buy", "sell"]
    nav: float
    shares: float
    amount: float
    fee: float
    note: Optional[str]
    created_at: str


class Position(BaseModel):
    """单基金持仓汇总（份额加权成本法）。"""

    fund_code: str
    fund_name: str
    shares: float = Field(..., description="剩余份额")
    cost_amount: float = Field(..., description="累计买入金额（已扣减卖出回款）")
    avg_cost: float = Field(..., description="持仓均价")
    market_value: float = Field(..., description="当前市值 = shares × latest_nav")
    profit: float = Field(..., description="累计收益")
    profit_rate: float = Field(..., description="累计收益率")
    today_profit: Optional[float] = Field(None, description="今日预估收益")
    today_profit_rate: Optional[float] = Field(None, description="今日预估收益率")
    latest_nav: float
    latest_nav_date: str
    estimated_nav: Optional[float] = None
    estimated_growth: Optional[float] = None


class HoldingsSummary(BaseModel):
    total_market_value: float
    total_cost: float
    total_profit: float
    total_profit_rate: float
    today_profit: float
    positions: list[Position]
