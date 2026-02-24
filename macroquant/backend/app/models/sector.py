"""板块数据模型"""
from sqlalchemy import Column, Integer, String, Date, Numeric, Index, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Sector(Base, TimestampMixin):
    """板块信息表"""
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # 板块代码
    name = Column(String(100), nullable=False)  # 板块名称
    sector_type = Column(String(20), nullable=False)  # 板块类型：industry-行业, concept-概念, region-地域

    # 关联的日数据
    daily_data = relationship("SectorDaily", back_populates="sector", cascade="all, delete-orphan")


class SectorDaily(Base, TimestampMixin):
    """板块日数据表"""
    __tablename__ = "sector_daily"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sector_id = Column(Integer, ForeignKey("sectors.id"), nullable=False)
    trade_date = Column(Date, nullable=False)

    # 涨跌数据
    change_pct = Column(Numeric(10, 4))  # 涨跌幅
    change_amount = Column(Numeric(20, 4))  # 涨跌额

    # 资金数据
    net_inflow = Column(Numeric(20, 4))  # 净流入（万元）
    main_inflow = Column(Numeric(20, 4))  # 主力净流入（万元）
    retail_inflow = Column(Numeric(20, 4))  # 散户净流入（万元）

    # 成交数据
    total_amount = Column(Numeric(20, 4))  # 总成交额（万元）
    total_volume = Column(Numeric(20, 4))  # 总成交量（万股）

    # 领涨股
    leading_stock = Column(String(20))  # 领涨股代码
    leading_stock_name = Column(String(100))  # 领涨股名称
    leading_change_pct = Column(Numeric(10, 4))  # 领涨股涨跌幅

    # 家数统计
    up_count = Column(Integer, default=0)  # 上涨家数
    down_count = Column(Integer, default=0)  # 下跌家数
    flat_count = Column(Integer, default=0)  # 平盘家数

    sector = relationship("Sector", back_populates="daily_data")

    __table_args__ = (
        Index('idx_sector_daily_sector_date', 'sector_id', 'trade_date', unique=True),
    )
