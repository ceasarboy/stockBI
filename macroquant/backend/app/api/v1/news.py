from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.news import (
    NewsCategory, NewsCategoryCreate,
    NewsItem, NewsItemCreate, NewsItemUpdate,
    ImpactPrediction, ImpactPredictionCreate, ImpactPredictionUpdate
)
from app.services.news_service import NewsService

router = APIRouter()


@router.post("/categories", response_model=NewsCategory, status_code=status.HTTP_201_CREATED)
async def create_category(category: NewsCategoryCreate, db: AsyncSession = Depends(get_db)):
    return await NewsService.create_category(db, category)


@router.get("/categories", response_model=List[NewsCategory])
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await NewsService.get_categories(db, skip=skip, limit=limit)


@router.get("/categories/{category_id}", response_model=NewsCategory)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await NewsService.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=NewsItem, status_code=status.HTTP_201_CREATED)
async def create_news(news: NewsItemCreate, db: AsyncSession = Depends(get_db)):
    return await NewsService.create_news(db, news)


@router.get("/", response_model=List[NewsItem])
async def get_news_list(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await NewsService.get_news_list(db, skip=skip, limit=limit)


@router.get("/{news_id}", response_model=NewsItem)
async def get_news(news_id: int, db: AsyncSession = Depends(get_db)):
    news = await NewsService.get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news


@router.put("/{news_id}", response_model=NewsItem)
async def update_news(news_id: int, news_update: NewsItemUpdate, db: AsyncSession = Depends(get_db)):
    news = await NewsService.update_news(db, news_id, news_update)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news


@router.post("/{news_id}/predictions", response_model=ImpactPrediction, status_code=status.HTTP_201_CREATED)
async def create_prediction(prediction: ImpactPredictionCreate, db: AsyncSession = Depends(get_db)):
    return await NewsService.create_prediction(db, prediction)


@router.get("/{news_id}/predictions", response_model=List[ImpactPrediction])
async def get_predictions(news_id: int, db: AsyncSession = Depends(get_db)):
    return await NewsService.get_predictions_by_news(db, news_id)


@router.get("/predictions/{prediction_id}", response_model=ImpactPrediction)
async def get_prediction(prediction_id: int, db: AsyncSession = Depends(get_db)):
    prediction = await NewsService.get_prediction(db, prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@router.put("/predictions/{prediction_id}", response_model=ImpactPrediction)
async def update_prediction(prediction_id: int, prediction_update: ImpactPredictionUpdate, db: AsyncSession = Depends(get_db)):
    prediction = await NewsService.update_prediction(db, prediction_id, prediction_update)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction
