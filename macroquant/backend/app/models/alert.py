from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from enum import Enum
from app.models.base import Base, TimestampMixin


class AlertConditionType(str, Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CROSS_ABOVE = "price_cross_above"
    PRICE_CROSS_BELOW = "price_cross_below"
    CHANGE_PCT_ABOVE = "change_pct_above"
    CHANGE_PCT_BELOW = "change_pct_below"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    TRIGGERED = "triggered"
    EXPIRED = "expired"


class AlertRule(Base, TimestampMixin):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("macro_instruments.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    condition_type = Column(SQLEnum(AlertConditionType), nullable=False)
    condition_params = Column(JSON, nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False)
    is_repeatable = Column(Boolean, default=False, nullable=False)
    cooldown_minutes = Column(Integer, default=60)
    last_triggered_at = Column(DateTime)
    expires_at = Column(DateTime)
    notification_channels = Column(JSON, default=list)

    user = relationship("User", back_populates="alert_rules")
    instrument = relationship("MacroInstrument", back_populates="alert_rules")
    alert_logs = relationship("AlertLog", back_populates="alert_rule", cascade="all, delete-orphan")


class AlertLog(Base):
    __tablename__ = "alert_logs"
    __table_args__ = (
        Index("idx_alert_rule_time", "alert_rule_id", "triggered_at"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    triggered_at = Column(DateTime, nullable=False, index=True)
    trigger_price = Column(Numeric(20, 8), nullable=False)
    message = Column(Text)
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime)

    alert_rule = relationship("AlertRule", back_populates="alert_logs")
