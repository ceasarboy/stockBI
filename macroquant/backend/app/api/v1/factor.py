from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.factor import FactorFamily
from app.schemas.factor import (
    FactorDefinition, FactorDefinitionCreate,
    FactorValue, FactorValueCreate,
    FactorCombination, FactorCombinationCreate,
    FactorBacktest, FactorBacktestCreate,
    FactorCalculationRequest, FactorCalculationResponse,
    StockSelectionRequest, StockSelectionResponse
)
from app.services.factor_service import FactorService

router = APIRouter()


@router.post("/definitions", response_model=FactorDefinition, status_code=status.HTTP_201_CREATED)
async def create_factor(factor: FactorDefinitionCreate, db: AsyncSession = Depends(get_db)):
    return await FactorService.create_factor(db, factor)


@router.get("/definitions", response_model=List[FactorDefinition])
async def get_factors(
    family: Optional[FactorFamily] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await FactorService.get_factors(db, family=family, skip=skip, limit=limit)


@router.get("/definitions/{factor_id}", response_model=FactorDefinition)
async def get_factor(factor_id: int, db: AsyncSession = Depends(get_db)):
    factor = await FactorService.get_factor(db, factor_id)
    if not factor:
        raise HTTPException(status_code=404, detail="Factor not found")
    return factor


@router.post("/values", response_model=FactorValue, status_code=status.HTTP_201_CREATED)
async def create_factor_value(value: FactorValueCreate, db: AsyncSession = Depends(get_db)):
    return await FactorService.calculate_and_store_factor_values(
        db, value.factor_id, value.stock_id, value.trade_date, value.value
    )


@router.get("/values/{factor_id}/{trade_date}", response_model=List[FactorValue])
async def get_factor_values(
    factor_id: int,
    trade_date: date,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await FactorService.get_factor_values(db, factor_id, trade_date, skip=skip, limit=limit)


@router.post("/values/{factor_id}/{trade_date}/rank")
async def rank_factor_values(factor_id: int, trade_date: date, db: AsyncSession = Depends(get_db)):
    values = await FactorService.calculate_factor_rankings(db, factor_id, trade_date)
    return {"factor_id": factor_id, "trade_date": trade_date, "count": len(values)}


@router.post("/combinations", response_model=FactorCombination, status_code=status.HTTP_201_CREATED)
async def create_combination(combination: FactorCombinationCreate, db: AsyncSession = Depends(get_db)):
    return await FactorService.create_combination(db, combination)


@router.get("/combinations", response_model=List[FactorCombination])
async def get_combinations(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await FactorService.get_combinations(db, skip=skip, limit=limit)


@router.get("/combinations/{combination_id}", response_model=FactorCombination)
async def get_combination(combination_id: int, db: AsyncSession = Depends(get_db)):
    combination = await FactorService.get_combination(db, combination_id)
    if not combination:
        raise HTTPException(status_code=404, detail="Combination not found")
    return combination


@router.post("/combinations/{combination_id}/select", response_model=StockSelectionResponse)
async def select_stocks(
    combination_id: int,
    trade_date: date,
    top_n: int = 10,
    db: AsyncSession = Depends(get_db)
):
    selected = await FactorService.select_stocks_by_combination(db, combination_id, trade_date, top_n)
    return StockSelectionResponse(
        combination_id=combination_id,
        trade_date=trade_date,
        selected_stocks=selected
    )


@router.post("/backtests", response_model=FactorBacktest, status_code=status.HTTP_201_CREATED)
async def create_backtest(backtest: FactorBacktestCreate, db: AsyncSession = Depends(get_db)):
    return await FactorService.create_backtest(db, backtest)


@router.get("/backtests/{backtest_id}", response_model=FactorBacktest)
async def get_backtest(backtest_id: int, db: AsyncSession = Depends(get_db)):
    backtest = await FactorService.get_backtest(db, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return backtest


@router.post("/screen")
async def screen_stocks(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """简单因子筛选"""
    from sqlalchemy import select, func
    from app.models.stock import Stock, StockDaily
    
    factor = request.get('factor', 'pe')
    operator = request.get('operator', 'gt')
    value = request.get('value', 0)
    sort = request.get('sort', 'desc')
    limit = request.get('limit', 20)
    
    # 获取最新交易日
    result = await db.execute(
        select(StockDaily.trade_date)
        .order_by(StockDaily.trade_date.desc())
        .limit(1)
    )
    latest_date = result.scalar_one_or_none()
    
    if not latest_date:
        return {"stocks": [], "total": 0}
    
    # 构建查询
    query = select(Stock, StockDaily).join(
        StockDaily, Stock.id == StockDaily.stock_id
    ).where(StockDaily.trade_date == latest_date)
    
    # 根据因子筛选
    if factor == 'pe' and hasattr(StockDaily, 'pe_ratio'):
        if operator == 'gt':
            query = query.where(StockDaily.pe_ratio > value)
        elif operator == 'lt':
            query = query.where(StockDaily.pe_ratio < value)
    elif factor == 'pb' and hasattr(StockDaily, 'pb_ratio'):
        if operator == 'gt':
            query = query.where(StockDaily.pb_ratio > value)
        elif operator == 'lt':
            query = query.where(StockDaily.pb_ratio < value)
    elif factor == 'turnover' and hasattr(StockDaily, 'turnover_rate'):
        if operator == 'gt':
            query = query.where(StockDaily.turnover_rate > value)
        elif operator == 'lt':
            query = query.where(StockDaily.turnover_rate < value)
    elif factor == 'market_cap':
        if operator == 'gt':
            query = query.where(StockDaily.amount > value * 100000000)
        elif operator == 'lt':
            query = query.where(StockDaily.amount < value * 100000000)
    
    # 排序
    if sort == 'desc':
        query = query.order_by(StockDaily.amount.desc())
    else:
        query = query.order_by(StockDaily.amount.asc())
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    items = result.all()
    
    stocks = []
    for stock, daily in items:
        factor_value = None
        if factor == 'pe' and daily.pe_ratio:
            factor_value = float(daily.pe_ratio)
        elif factor == 'pb' and daily.pb_ratio:
            factor_value = float(daily.pb_ratio)
        elif factor == 'turnover' and daily.turnover_rate:
            factor_value = float(daily.turnover_rate)
        elif factor == 'market_cap' and daily.amount:
            factor_value = float(daily.amount) / 100000000
        
        stocks.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "value": factor_value
        })
    
    return {"stocks": stocks, "total": len(stocks)}
