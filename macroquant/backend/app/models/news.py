from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from enum import Enum
from app.models.base import Base, TimestampMixin


class NewsCategory(Base, TimestampMixin):
    __tablename__ = "news_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200))

    news_items = relationship("NewsItem", back_populates="category", cascade="all, delete-orphan")


class TimeHorizon(str, Enum):
    SHORT_TERM = "短期 (1-5天)"
    MID_TERM = "中期 (1-3个月)"
    LONG_TERM = "长期 (3个月以上)"


class PredictionStatus(str, Enum):
    PENDING = "观察中"
    VALIDATED_SUCCESS = "逻辑兑现"
    VALIDATED_FAIL = "逻辑证伪"


class NewsItem(Base, TimestampMixin):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("news_categories.id"))
    title = Column(String(200), nullable=False)
    content = Column(Text)
    source_url = Column(String(255))
    publish_time = Column(DateTime, nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))

    category = relationship("NewsCategory", back_populates="news_items")
    author = relationship("User")
    predictions = relationship("ImpactPrediction", back_populates="news", cascade="all, delete-orphan")


class ImpactPrediction(Base, TimestampMixin):
    __tablename__ = "impact_predictions"
    __table_args__ = (
        Index("idx_news_prediction", "news_id"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey("news_items.id"), nullable=False)
    target_asset = Column(String(100), nullable=False)
    impact_score = Column(Integer, nullable=False)
    time_horizon = Column(SQLEnum(TimeHorizon), nullable=False)
    rationale = Column(Text)
    status = Column(SQLEnum(PredictionStatus), default=PredictionStatus.PENDING, nullable=False)
    actual_impact_notes = Column(Text)
    review_time = Column(DateTime)

    news = relationship("NewsItem", back_populates="predictions")
