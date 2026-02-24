from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.models.indicator import TechnicalIndicator

router = APIRouter()


class TechnicalIndicatorCreate(BaseModel):
    name: str
    category: str = 'technical'
    indicator_type: str
    params: dict = {}
    color: str = '#f59e0b'
    line_style: str = 'solid'
    line_width: int = 1
    description: Optional[str] = None


class TechnicalIndicatorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    params: Optional[dict] = None
    color: Optional[str] = None
    line_style: Optional[str] = None
    line_width: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class TechnicalIndicatorResponse(BaseModel):
    id: int
    name: str
    category: str
    indicator_type: str
    params: dict
    color: str
    line_style: str
    line_width: int
    is_active: bool
    display_order: int
    description: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TechnicalIndicatorResponse])
async def get_indicators(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(TechnicalIndicator).order_by(TechnicalIndicator.display_order, TechnicalIndicator.id)
    
    if category:
        query = query.where(TechnicalIndicator.category == category)
    if is_active is not None:
        query = query.where(TechnicalIndicator.is_active == is_active)
    
    result = await db.execute(query)
    indicators = result.scalars().all()
    
    if not indicators:
        for indicator_data in TechnicalIndicator.BUILTIN_INDICATORS:
            indicator = TechnicalIndicator(**indicator_data)
            db.add(indicator)
        await db.commit()
        result = await db.execute(query)
        indicators = result.scalars().all()
    
    return indicators


@router.get("/categories", response_model=List[str])
async def get_indicator_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TechnicalIndicator.category).distinct().order_by(TechnicalIndicator.category)
    )
    categories = [row[0] for row in result.all()]
    if not categories:
        categories = ['trend', 'momentum', 'volume', 'volatility']
    return categories


@router.get("/types", response_model=List[dict])
async def get_indicator_types():
    return [
        {'type': 'MA', 'name': '移动平均线', 'params': ['period'], 'category': 'trend'},
        {'type': 'EMA', 'name': '指数移动平均线', 'params': ['period'], 'category': 'trend'},
        {'type': 'VOL', 'name': '成交量', 'params': [], 'category': 'volume'},
        {'type': 'MACD', 'name': 'MACD指标', 'params': ['fast', 'slow', 'signal'], 'category': 'momentum'},
        {'type': 'KDJ', 'name': 'KDJ指标', 'params': ['n', 'm1', 'm2'], 'category': 'momentum'},
        {'type': 'RSI', 'name': '相对强弱指标', 'params': ['period'], 'category': 'momentum'},
        {'type': 'ORB', 'name': '开盘区间突破', 'params': ['period'], 'category': 'volatility'},
        {'type': 'BOLL', 'name': '布林带', 'params': ['period', 'std_dev'], 'category': 'volatility'},
        {'type': 'ATR', 'name': '平均真实波幅', 'params': ['period'], 'category': 'volatility'},
    ]


@router.get("/{indicator_id}", response_model=TechnicalIndicatorResponse)
async def get_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TechnicalIndicator).where(TechnicalIndicator.id == indicator_id))
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator


@router.post("/", response_model=TechnicalIndicatorResponse)
async def create_indicator(indicator_data: TechnicalIndicatorCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TechnicalIndicator).where(TechnicalIndicator.name == indicator_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Indicator name already exists")
    
    max_order_result = await db.execute(
        select(TechnicalIndicator.display_order).order_by(TechnicalIndicator.display_order.desc()).limit(1)
    )
    max_order = max_order_result.scalar() or 0
    
    indicator = TechnicalIndicator(
        name=indicator_data.name,
        category=indicator_data.category,
        indicator_type=indicator_data.indicator_type,
        params=indicator_data.params,
        color=indicator_data.color,
        line_style=indicator_data.line_style,
        line_width=indicator_data.line_width,
        description=indicator_data.description,
        display_order=max_order + 1
    )
    db.add(indicator)
    await db.commit()
    await db.refresh(indicator)
    return indicator


@router.put("/{indicator_id}", response_model=TechnicalIndicatorResponse)
async def update_indicator(
    indicator_id: int,
    indicator_data: TechnicalIndicatorUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(TechnicalIndicator).where(TechnicalIndicator.id == indicator_id))
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    update_data = indicator_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(indicator, key, value)
    
    await db.commit()
    await db.refresh(indicator)
    return indicator


@router.delete("/{indicator_id}")
async def delete_indicator(indicator_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TechnicalIndicator).where(TechnicalIndicator.id == indicator_id))
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    
    await db.execute(delete(TechnicalIndicator).where(TechnicalIndicator.id == indicator_id))
    await db.commit()
    return {"status": "success", "message": f"Indicator {indicator.name} deleted"}


@router.post("/reset")
async def reset_indicators(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(TechnicalIndicator))
    
    for indicator_data in TechnicalIndicator.BUILTIN_INDICATORS:
        indicator = TechnicalIndicator(**indicator_data)
        db.add(indicator)
    
    await db.commit()
    return {"status": "success", "message": "Indicators reset to defaults"}
