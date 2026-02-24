import enum
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from app.models.base import Base, TimestampMixin


class FactorFamily(str, enum.Enum):
    value = 'value'
    momentum = 'momentum'
    volatility = 'volatility'
    valuation = 'valuation'
    technical = 'technical'


class BacktestStatus(str, enum.Enum):
    pending = 'pending'
    running = 'running'
    completed = 'completed'
    failed = 'failed'


class FactorDefinition(Base, TimestampMixin):
    __tablename__ = "factor_definitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    family = Column(String(20), nullable=False)
    description = Column(String(500))
    formula = Column(String(1000))
    params = Column(String(500))
    is_active = Column(Integer, default=1)


class FactorValue(Base, TimestampMixin):
    __tablename__ = "factor_values"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    factor_id = Column(Integer, ForeignKey("factor_definitions.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    value = Column(Numeric(20, 6))
    rank = Column(Integer)
    percentile = Column(Numeric(10, 4))


class FactorCombination(Base, TimestampMixin):
    __tablename__ = "factor_combinations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    factors = Column(String(500))
    weights = Column(String(500))
    author_id = Column(Integer)
    is_public = Column(Integer, default=1)


class FactorBacktest(Base, TimestampMixin):
    __tablename__ = "factor_backtests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    combination_id = Column(Integer, ForeignKey("factor_combinations.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    rebalance_freq = Column(String(20), default="monthly")
    top_n = Column(Integer, default=10)
    status = Column(String(20), default="pending")
    results = Column(String(5000))
    metrics = Column(String(5000))
    error_message = Column(String(1000))
    started_at = Column(Date)
    completed_at = Column(Date)
