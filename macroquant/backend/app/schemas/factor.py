from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, date
from app.models.factor import FactorFamily, BacktestStatus


class FactorDefinitionBase(BaseModel):
    name: str
    family: FactorFamily
    description: Optional[str] = None
    formula: Optional[str] = None
    params: Optional[Dict] = None


class FactorDefinitionCreate(FactorDefinitionBase):
    pass


class FactorDefinition(FactorDefinitionBase):
    id: int
    is_active: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FactorValueBase(BaseModel):
    factor_id: int
    stock_id: int
    trade_date: date
    value: float
    rank: Optional[int] = None
    percentile: Optional[float] = None


class FactorValueCreate(FactorValueBase):
    pass


class FactorValue(FactorValueBase):
    id: int

    class Config:
        from_attributes = True


class FactorCombinationBase(BaseModel):
    name: str
    description: Optional[str] = None
    factors: List[int]
    weights: Optional[List[float]] = None


class FactorCombinationCreate(FactorCombinationBase):
    pass


class FactorCombination(FactorCombinationBase):
    id: int
    author_id: Optional[int] = None
    is_public: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FactorBacktestBase(BaseModel):
    combination_id: int
    start_date: date
    end_date: date
    rebalance_freq: str = "monthly"
    top_n: int = 10


class FactorBacktestCreate(FactorBacktestBase):
    pass


class FactorBacktest(FactorBacktestBase):
    id: int
    status: BacktestStatus
    results: Optional[Dict] = None
    metrics: Optional[Dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FactorCalculationRequest(BaseModel):
    factor_name: str
    stock_ids: Optional[List[int]] = None
    start_date: date
    end_date: date


class FactorCalculationResponse(BaseModel):
    factor_name: str
    trade_date: date
    values: List[FactorValue]


class StockSelectionRequest(BaseModel):
    combination_id: int
    trade_date: date
    top_n: int = 10


class StockSelectionResponse(BaseModel):
    combination_id: int
    trade_date: date
    selected_stocks: List[Dict]
