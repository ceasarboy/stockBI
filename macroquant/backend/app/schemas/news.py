from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from app.models.news import TimeHorizon, PredictionStatus


class NewsCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class NewsCategoryCreate(NewsCategoryBase):
    pass


class NewsCategory(NewsCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NewsItemBase(BaseModel):
    category_id: Optional[int] = None
    title: str
    content: Optional[str] = None
    source_url: Optional[str] = None
    publish_time: datetime


class NewsItemCreate(NewsItemBase):
    pass


class NewsItemUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[str] = None
    publish_time: Optional[datetime] = None


class NewsItem(NewsItemBase):
    id: int
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    category: Optional[NewsCategory] = None
    predictions: List["ImpactPrediction"] = []

    class Config:
        from_attributes = True


class ImpactPredictionBase(BaseModel):
    news_id: int
    target_asset: str
    impact_score: int
    time_horizon: TimeHorizon
    rationale: Optional[str] = None


class ImpactPredictionCreate(ImpactPredictionBase):
    pass


class ImpactPredictionUpdate(BaseModel):
    target_asset: Optional[str] = None
    impact_score: Optional[int] = None
    time_horizon: Optional[TimeHorizon] = None
    rationale: Optional[str] = None
    status: Optional[PredictionStatus] = None
    actual_impact_notes: Optional[str] = None
    review_time: Optional[datetime] = None


class ImpactPrediction(ImpactPredictionBase):
    id: int
    status: PredictionStatus
    actual_impact_notes: Optional[str] = None
    review_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


NewsItem.model_rebuild()
