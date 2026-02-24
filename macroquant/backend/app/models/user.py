from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
from app.models.base import Base, TimestampMixin


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)

    alert_rules = relationship("AlertRule", back_populates="user", cascade="all, delete-orphan")
    news_items = relationship("NewsItem", back_populates="author", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="author", cascade="all, delete-orphan")
