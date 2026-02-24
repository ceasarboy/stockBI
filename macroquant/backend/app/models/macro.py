from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from enum import Enum
from app.models.base import Base, TimestampMixin


class MacroType(str, Enum):
    FUTURE = "future"
    FX = "fx"
    COMMODITY = "commodity"
    BOND = "bond"
    INDEX = "index"


class MacroInstrument(Base, TimestampMixin):
    __tablename__ = "macro_instruments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(MacroType), nullable=False, index=True)
    exchange = Column(String(50))
    currency = Column(String(10), default="USD")
    price_precision = Column(Integer, default=2)
    is_active = Column(Integer, default=1, nullable=False)
    data_source = Column(String(50))

    ticks = relationship("MacroTick", back_populates="instrument", cascade="all, delete-orphan")
    bars = relationship("MacroBar", back_populates="instrument", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="instrument", cascade="all, delete-orphan")


class MacroTick(Base):
    __tablename__ = "macro_ticks"
    __table_args__ = (
        Index("idx_macro_tick_time", "instrument_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("macro_instruments.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 2))

    instrument = relationship("MacroInstrument", back_populates="ticks")


class BarPeriod(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class MacroBar(Base):
    __tablename__ = "macro_bars"
    __table_args__ = (
        Index("idx_macro_bar_period_time", "instrument_id", "period", "start_time", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("macro_instruments.id"), nullable=False)
    period = Column(SQLEnum(BarPeriod), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    open = Column(Numeric(20, 8), nullable=False)
    high = Column(Numeric(20, 8), nullable=False)
    low = Column(Numeric(20, 8), nullable=False)
    close = Column(Numeric(20, 8), nullable=False)
    volume = Column(Numeric(20, 2))
    num_trades = Column(Integer)

    instrument = relationship("MacroInstrument", back_populates="bars")
