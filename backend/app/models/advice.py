from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


SignalLevel = Literal["info", "watch", "buy", "sell"]


class AdviceSignal(BaseModel):
    name: str
    level: SignalLevel
    message: str
    value: Optional[float] = None


class FundAdvice(BaseModel):
    fund_code: str
    fund_name: str
    signals: list[AdviceSignal]
    percentile: Optional[float] = None
    ma_deviation: Optional[float] = None
    max_drawdown: Optional[float] = None
    profit_rate: Optional[float] = None
