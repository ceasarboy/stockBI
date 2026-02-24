from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.factor import Factor

router = APIRouter()


class FactorCreate(BaseModel):
    name: str
    category: str = 'technical'
    factor_type: str
    params: dict = {}
    color: str = '#f59e0b'
    line_style: str = 'solid'
    line_width: int = 1
    description: Optional[str] = None


class FactorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    params: Optional[dict] = None
    color: Optional[str] = None
    line_style: Optional[str] = None
    line_width: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class FactorResponse(BaseModel):
    id: int
    name: str
    category: str
    factor_type: str
    params: dict
    color: str
    line_style: str
    line_width: int
    is_active: bool
    display_order: int
    description: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[FactorResponse])
async def get_factors(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Factor).order_by(Factor.display_order, Factor.id)
    
    if category:
        query = query.where(Factor.category == category)
    if is_active is not None:
        query = query.where(Factor.is_active == is_active)
    
    result = await db.execute(query)
    factors = result.scalars().all()
    
    if not factors:
        for factor_data in Factor.BUILTIN_FACTORS:
            factor = Factor(**factor_data)
            db.add(factor)
        await db.commit()
        result = await db.execute(query)
        factors = result.scalars().all()
    
    return factors


@router.get("/categories", response_model=List[str])
async def get_factor_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Factor.category).distinct().order_by(Factor.category)
    )
    return [row[0] for row in result.all()]


@router.get("/types", response_model=List[str])
async def get_factor_types(db: AsyncSession = Depends(get_db)):
    return ['MA', 'EMA', 'VOL', 'MACD', 'KDJ', 'RSI', 'ORB', 'BOLL', 'SAR', 'ATR']


@router.get("/{factor_id}", response_model=FactorResponse)
async def get_factor(factor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Factor).where(Factor.id == factor_id))
    factor = result.scalar_one_or_none()
    if not factor:
        raise HTTPException(status_code=404, detail="Factor not found")
    return factor


@router.post("/", response_model=FactorResponse)
async def create_factor(factor_data: FactorCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Factor).where(Factor.name == factor_data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Factor name already exists")
    
    max_order_result = await db.execute(
        select(Factor.display_order).order_by(Factor.display_order.desc()).limit(1)
    )
    max_order = max_order_result.scalar() or 0
    
    factor = Factor(
        name=factor_data.name,
        category=factor_data.category,
        factor_type=factor_data.factor_type,
        params=factor_data.params,
        color=factor_data.color,
        line_style=factor_data.line_style,
        line_width=factor_data.line_width,
        description=factor_data.description,
        display_order=max_order + 1
    )
    db.add(factor)
    await db.commit()
    await db.refresh(factor)
    return factor


@router.put("/{factor_id}", response_model=FactorResponse)
async def update_factor(
    factor_id: int,
    factor_data: FactorUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Factor).where(Factor.id == factor_id))
    factor = result.scalar_one_or_none()
    if not factor:
        raise HTTPException(status_code=404, detail="Factor not found")
    
    update_data = factor_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(factor, key, value)
    
    await db.commit()
    await db.refresh(factor)
    return factor


@router.delete("/{factor_id}")
async def delete_factor(factor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Factor).where(Factor.id == factor_id))
    factor = result.scalar_one_or_none()
    if not factor:
        raise HTTPException(status_code=404, detail="Factor not found")
    
    await db.execute(delete(Factor).where(Factor.id == factor_id))
    await db.commit()
    return {"status": "success", "message": f"Factor {factor.name} deleted"}


@router.post("/reset")
async def reset_factors(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Factor))
    
    for factor_data in Factor.BUILTIN_FACTORS:
        factor = Factor(**factor_data)
        db.add(factor)
    
    await db.commit()
    return {"status": "success", "message": "Factors reset to defaults"}
