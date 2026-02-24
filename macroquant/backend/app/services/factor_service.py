from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np
import pandas as pd
from datetime import date
from app.models.factor import FactorDefinition, FactorValue, FactorFamily, FactorCombination, FactorBacktest
from app.models.stock import StockDaily
from app.schemas.factor import FactorDefinitionCreate, FactorCombinationCreate, FactorBacktestCreate


class FactorCalculator:
    @staticmethod
    def calculate_pe(close: float, eps: float) -> Optional[float]:
        if eps and eps > 0:
            return close / eps
        return None

    @staticmethod
    def calculate_pb(close: float, bvps: float) -> Optional[float]:
        if bvps and bvps > 0:
            return close / bvps
        return None

    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> Optional[float]:
        if len(prices) < period + 1:
            return None
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        if len(prices) < slow + signal:
            return {"macd": None, "signal": None, "histogram": None}
        ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
        ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "macd": float(macd_line.iloc[-1]),
            "signal": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }

    @staticmethod
    def calculate_volatility(returns: np.ndarray, period: int = 20) -> Optional[float]:
        if len(returns) < period:
            return None
        return float(np.std(returns[-period:]) * np.sqrt(252))

    @staticmethod
    def calculate_return(prices: np.ndarray, period: int) -> Optional[float]:
        if len(prices) < period + 1:
            return None
        return float((prices[-1] - prices[-period - 1]) / prices[-period - 1])

    @staticmethod
    def calculate_moving_average(prices: np.ndarray, period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        return float(np.mean(prices[-period:]))

    @staticmethod
    def calculate_correlation(series1: np.ndarray, series2: np.ndarray) -> Optional[float]:
        if len(series1) != len(series2) or len(series1) < 2:
            return None
        return float(np.corrcoef(series1, series2)[0, 1])


class FactorService:
    @staticmethod
    async def create_factor(db: AsyncSession, factor: FactorDefinitionCreate) -> FactorDefinition:
        db_factor = FactorDefinition(**factor.model_dump())
        db.add(db_factor)
        await db.commit()
        await db.refresh(db_factor)
        return db_factor

    @staticmethod
    async def get_factors(db: AsyncSession, family: Optional[FactorFamily] = None, skip: int = 0, limit: int = 100) -> List[FactorDefinition]:
        query = select(FactorDefinition)
        if family:
            query = query.where(FactorDefinition.family == family)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_factor(db: AsyncSession, factor_id: int) -> Optional[FactorDefinition]:
        result = await db.execute(select(FactorDefinition).where(FactorDefinition.id == factor_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def calculate_and_store_factor_values(
        db: AsyncSession,
        factor_id: int,
        stock_id: int,
        trade_date: date,
        value: float
    ) -> FactorValue:
        db_value = FactorValue(
            factor_id=factor_id,
            stock_id=stock_id,
            trade_date=trade_date,
            value=value
        )
        db.add(db_value)
        await db.commit()
        await db.refresh(db_value)
        return db_value

    @staticmethod
    async def get_factor_values(
        db: AsyncSession,
        factor_id: int,
        trade_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> List[FactorValue]:
        result = await db.execute(
            select(FactorValue)
            .where(FactorValue.factor_id == factor_id)
            .where(FactorValue.trade_date == trade_date)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_combination(db: AsyncSession, combination: FactorCombinationCreate, author_id: Optional[int] = None) -> FactorCombination:
        db_combination = FactorCombination(**combination.model_dump(), author_id=author_id)
        db.add(db_combination)
        await db.commit()
        await db.refresh(db_combination)
        return db_combination

    @staticmethod
    async def get_combinations(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[FactorCombination]:
        result = await db.execute(select(FactorCombination).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_combination(db: AsyncSession, combination_id: int) -> Optional[FactorCombination]:
        result = await db.execute(select(FactorCombination).where(FactorCombination.id == combination_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_backtest(db: AsyncSession, backtest: FactorBacktestCreate) -> FactorBacktest:
        db_backtest = FactorBacktest(**backtest.model_dump())
        db.add(db_backtest)
        await db.commit()
        await db.refresh(db_backtest)
        return db_backtest

    @staticmethod
    async def get_backtest(db: AsyncSession, backtest_id: int) -> Optional[FactorBacktest]:
        result = await db.execute(select(FactorBacktest).where(FactorBacktest.id == backtest_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def calculate_factor_rankings(db: AsyncSession, factor_id: int, trade_date: date) -> List[FactorValue]:
        values = await FactorService.get_factor_values(db, factor_id, trade_date, limit=5000)
        if not values:
            return []
        sorted_values = sorted(values, key=lambda x: x.value, reverse=True)
        total = len(sorted_values)
        for i, v in enumerate(sorted_values):
            v.rank = i + 1
            v.percentile = (total - i) / total * 100
        await db.commit()
        return sorted_values

    @staticmethod
    async def select_stocks_by_combination(
        db: AsyncSession,
        combination_id: int,
        trade_date: date,
        top_n: int = 10
    ) -> List[Dict]:
        combination = await FactorService.get_combination(db, combination_id)
        if not combination:
            return []
        factor_ids = combination.factors
        weights = combination.weights or [1.0 / len(factor_ids)] * len(factor_ids)
        all_values = {}
        for factor_id in factor_ids:
            values = await FactorService.get_factor_values(db, factor_id, trade_date, limit=5000)
            for v in values:
                if v.stock_id not in all_values:
                    all_values[v.stock_id] = 0.0
                all_values[v.stock_id] += v.percentile * weights[factor_ids.index(factor_id)]
        sorted_stocks = sorted(all_values.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"stock_id": s[0], "score": s[1]} for s in sorted_stocks]
