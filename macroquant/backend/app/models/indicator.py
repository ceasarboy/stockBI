from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.models.base import Base, TimestampMixin


class TechnicalIndicator(Base, TimestampMixin):
    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    category = Column(String(20), nullable=False, default='technical')
    indicator_type = Column(String(20), nullable=False)
    params = Column(JSON, default={})
    color = Column(String(20), default='#f59e0b')
    line_style = Column(String(20), default='solid')
    line_width = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    description = Column(String(500))

    BUILTIN_INDICATORS = [
        {
            'name': 'MA5',
            'category': 'trend',
            'indicator_type': 'MA',
            'params': {'period': 5},
            'color': '#f59e0b',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 1
        },
        {
            'name': 'MA10',
            'category': 'trend',
            'indicator_type': 'MA',
            'params': {'period': 10},
            'color': '#3b82f6',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 2
        },
        {
            'name': 'MA20',
            'category': 'trend',
            'indicator_type': 'MA',
            'params': {'period': 20},
            'color': '#8b5cf6',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 3
        },
        {
            'name': 'MA30',
            'category': 'trend',
            'indicator_type': 'MA',
            'params': {'period': 30},
            'color': '#ec4899',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 4
        },
        {
            'name': '成交量',
            'category': 'volume',
            'indicator_type': 'VOL',
            'params': {},
            'color': '#ef232a',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 10
        },
        {
            'name': 'MACD',
            'category': 'momentum',
            'indicator_type': 'MACD',
            'params': {'fast': 12, 'slow': 26, 'signal': 9},
            'color': '#f59e0b',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 20
        },
        {
            'name': 'KDJ',
            'category': 'momentum',
            'indicator_type': 'KDJ',
            'params': {'n': 9, 'm1': 3, 'm2': 3},
            'color': '#f59e0b',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 21
        },
        {
            'name': 'RSI',
            'category': 'momentum',
            'indicator_type': 'RSI',
            'params': {'period': 14},
            'color': '#f59e0b',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 22
        },
        {
            'name': 'ORB',
            'category': 'volatility',
            'indicator_type': 'ORB',
            'params': {'period': 20},
            'color': '#ef232a',
            'line_style': 'solid',
            'line_width': 1,
            'display_order': 30
        },
    ]
