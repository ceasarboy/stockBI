from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Text, Enum as SQLEnum, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from enum import Enum
from app.models.base import Base, TimestampMixin


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Strategy(Base, TimestampMixin):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)
    parameters = Column(JSON)
    status = Column(SQLEnum(StrategyStatus), default=StrategyStatus.DRAFT, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Integer, default=0, nullable=False)

    author = relationship("User", back_populates="strategies")
    backtests = relationship("StrategyBacktest", back_populates="strategy", cascade="all, delete-orphan")


class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StrategyBacktest(Base, TimestampMixin):
    __tablename__ = "strategy_backtests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String(200))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Numeric(20, 2), nullable=False)
    parameters = Column(JSON)
    status = Column(SQLEnum(BacktestStatus), default=BacktestStatus.PENDING, nullable=False)
    results = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    strategy = relationship("Strategy", back_populates="backtests")
