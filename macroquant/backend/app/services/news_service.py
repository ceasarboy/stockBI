from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.news import NewsCategory, NewsItem, ImpactPrediction
from app.schemas.news import NewsCategoryCreate, NewsItemCreate, NewsItemUpdate, ImpactPredictionCreate, ImpactPredictionUpdate


class NewsService:
    @staticmethod
    async def create_category(db: AsyncSession, category: NewsCategoryCreate) -> NewsCategory:
        db_category = NewsCategory(**category.model_dump())
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)
        return db_category

    @staticmethod
    async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[NewsCategory]:
        result = await db.execute(select(NewsCategory).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_category(db: AsyncSession, category_id: int) -> Optional[NewsCategory]:
        result = await db.execute(select(NewsCategory).where(NewsCategory.id == category_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_news(db: AsyncSession, news: NewsItemCreate, author_id: Optional[int] = None) -> NewsItem:
        db_news = NewsItem(**news.model_dump(), author_id=author_id)
        db.add(db_news)
        await db.commit()
        await db.refresh(db_news)
        return db_news

    @staticmethod
    async def get_news_list(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[NewsItem]:
        result = await db.execute(select(NewsItem).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_news(db: AsyncSession, news_id: int) -> Optional[NewsItem]:
        result = await db.execute(select(NewsItem).where(NewsItem.id == news_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_news(db: AsyncSession, news_id: int, news_update: NewsItemUpdate) -> Optional[NewsItem]:
        db_news = await NewsService.get_news(db, news_id)
        if not db_news:
            return None
        update_data = news_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_news, field, value)
        await db.commit()
        await db.refresh(db_news)
        return db_news

    @staticmethod
    async def create_prediction(db: AsyncSession, prediction: ImpactPredictionCreate) -> ImpactPrediction:
        db_prediction = ImpactPrediction(**prediction.model_dump())
        db.add(db_prediction)
        await db.commit()
        await db.refresh(db_prediction)
        return db_prediction

    @staticmethod
    async def get_predictions_by_news(db: AsyncSession, news_id: int) -> List[ImpactPrediction]:
        result = await db.execute(select(ImpactPrediction).where(ImpactPrediction.news_id == news_id))
        return list(result.scalars().all())

    @staticmethod
    async def get_prediction(db: AsyncSession, prediction_id: int) -> Optional[ImpactPrediction]:
        result = await db.execute(select(ImpactPrediction).where(ImpactPrediction.id == prediction_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_prediction(db: AsyncSession, prediction_id: int, prediction_update: ImpactPredictionUpdate) -> Optional[ImpactPrediction]:
        db_prediction = await NewsService.get_prediction(db, prediction_id)
        if not db_prediction:
            return None
        update_data = prediction_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_prediction, field, value)
        await db.commit()
        await db.refresh(db_prediction)
        return db_prediction
