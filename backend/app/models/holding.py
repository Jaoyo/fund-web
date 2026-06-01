from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    """录入交易。amount 和 shares 至少给一个，缺的那个由 nav 算出。如果都不提供或 nav 未知，则进入待确认状态。"""

    client_id: Optional[str] = Field(None, description="幂等 ID，可选")
    fund_code: str
    date: str = Field(..., description="YYYY-MM-DD")
    type: Literal["buy", "sell", "import"]
    nav: Optional[float] = Field(None, gt=0, description="成交净值，为 null 时自动判定是否待确认")
    shares: Optional[float] = Field(None, gt=0)
    amount: Optional[float] = Field(None, gt=0)
    profit: Optional[float] = Field(None, description="当前累计收益，仅用于导入旧持仓")
    fund_name: Optional[str] = Field(None, description="基金名称，仅用于导入旧持仓时可选输入")
    fee: float = Field(0, ge=0)
    settlement_days: int = Field(1, description="交收周期，1为T+1，2为T+2")
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
    settlement_days: int
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
    today_profit: Optional[float] = Field(None, description="今日收益金额")
    today_profit_rate: Optional[float] = Field(None, description="今日收益率")
    is_estimated: bool = Field(True, description="为 true 表示今日收益是基于估算的；false 表示是盘后实际确认的")
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
    today_profit_rate: float
    is_estimated: bool = True
    update_status: Literal["estimated", "updating", "updated"] = "estimated"
    positions: list[Position]
    trade_date: str = Field(..., description="当前最新交易日")


class FundStockHolding(BaseModel):
    """基金持有的单只股票。"""
    stock_code: str
    stock_name: str
    proportion: float = Field(..., description="占净值比例（百分比，如 9.5 表示 9.5%）")


class FundContribution(BaseModel):
    fund_code: str
    fund_name: str
    market_value: float

class UserStockPosition(BaseModel):
    """穿透计算后，用户个人账户持有的单只重仓股。"""
    stock_code: str
    stock_name: str
    total_market_value: float = Field(..., description="穿透算出的个人持仓总市值")
    proportion: float = Field(..., description="占个人总股票/基金总资产的比例（百分比，如 15.2 表示 15.2%）")
    contributing_funds: list[FundContribution] = []
