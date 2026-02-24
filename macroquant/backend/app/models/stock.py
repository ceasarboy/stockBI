from sqlalchemy import Column, Integer, String, Date, Numeric, Index, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Stock(Base, TimestampMixin):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    name_pinyin = Column(String(100), index=True)  # 拼音首字母，如"英维克"->"ywk"
    exchange = Column(String(20), nullable=False)
    industry = Column(String(100))
    list_date = Column(Date)
    is_active = Column(Integer, default=1, nullable=False)
    stock_type = Column(String(20), default="A股", nullable=False)

    daily_data = relationship("StockDaily", back_populates="stock", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="stock", cascade="all, delete-orphan")


class StockDaily(Base):
    __tablename__ = "stock_daily"
    __table_args__ = (
        Index("idx_stock_date", "stock_id", "trade_date", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    trade_date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(10, 4))
    high = Column(Numeric(10, 4))
    low = Column(Numeric(10, 4))
    close = Column(Numeric(10, 4), nullable=False)
    volume = Column(Numeric(20, 2))
    amount = Column(Numeric(20, 2))
    turnover_rate = Column(Numeric(10, 4))
    pe_ratio = Column(Numeric(10, 4))
    pb_ratio = Column(Numeric(10, 4))
    change_pct = Column(Numeric(10, 4))

    stock = relationship("Stock", back_populates="daily_data")


class WatchlistItem(Base, TimestampMixin):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    notes = Column(String(500))

    stock = relationship("Stock", back_populates="watchlist_items")
