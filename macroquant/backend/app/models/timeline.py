from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Index
from app.models.base import Base, TimestampMixin


class StockTimeline(Base, TimestampMixin):
    """股票分时数据"""
    __tablename__ = "stock_timeline"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    trade_date = Column(DateTime, nullable=False)  # 交易日期时间
    price = Column(Numeric(10, 2), nullable=False)  # 当前价格
    volume = Column(Numeric(20, 0))  # 成交量
    amount = Column(Numeric(20, 2))  # 成交额
    avg_price = Column(Numeric(10, 2))  # 均价

    __table_args__ = (
        Index('idx_timeline_stock_date', 'stock_id', 'trade_date'),
    )
