"""数据相关API"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
import logging
import pandas as pd

from app.core.database import get_db
from app.services.stock_data_service import stock_data_service

router = APIRouter()
logger = logging.getLogger(__name__)


from pydantic import BaseModel


class SyncAllStocksRequest:
    def __init__(self, days: int = 30, mode: str = "incremental"):
        self.days = days
        self.mode = mode


class BatchSyncRequest(BaseModel):
    scope: str = "watchlist"
    days: int = 365
    mode: str = "full"


@router.get("/statistics")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func, select, or_
    from app.models.stock import Stock, StockDaily, WatchlistItem

    total_stocks = await db.execute(select(func.count(Stock.id)))
    total_stocks = total_stocks.scalar() or 0

    total_daily = await db.execute(select(func.count(StockDaily.id)))
    total_daily = total_daily.scalar() or 0

    watchlist_count = await db.execute(select(func.count(WatchlistItem.id)))
    watchlist_count = watchlist_count.scalar() or 0

    today = datetime.now().date()
    today_sync = await db.execute(
        select(func.count(StockDaily.id)).where(StockDaily.trade_date == today)
    )
    today_sync = today_sync.scalar() or 0

    # 今日同步股票数
    today_stocks_result = await db.execute(
        select(func.count(func.distinct(StockDaily.stock_id))).where(StockDaily.trade_date == today)
    )
    today_stocks = today_stocks_result.scalar() or 0

    # 上市板块分布
    board_distribution = {}
    result = await db.execute(
        select(Stock.exchange, func.count(Stock.id)).group_by(Stock.exchange)
    )
    for row in result:
        exchange = row[0]
        count = row[1]
        if exchange == 'SH':
            # 判断是主板还是科创板
            main_result = await db.execute(
                select(func.count(Stock.id)).where(
                    Stock.exchange == 'SH',
                    Stock.symbol.notlike('688%')
                )
            )
            main_count = main_result.scalar() or 0
            star_result = await db.execute(
                select(func.count(Stock.id)).where(
                    Stock.exchange == 'SH',
                    Stock.symbol.like('688%')
                )
            )
            star_count = star_result.scalar() or 0
            board_distribution['上证主板'] = main_count
            board_distribution['科创板'] = star_count
        elif exchange == 'SZ':
            # 判断是主板还是创业板（创业板包括300和301开头）
            gem_result = await db.execute(
                select(func.count(Stock.id)).where(
                    or_(
                        Stock.symbol.like('300%'),
                        Stock.symbol.like('301%')
                    )
                )
            )
            gem_count = gem_result.scalar() or 0
            main_result = await db.execute(
                select(func.count(Stock.id)).where(
                    Stock.exchange == 'SZ',
                    Stock.symbol.notlike('300%'),
                    Stock.symbol.notlike('301%')
                )
            )
            main_count = main_result.scalar() or 0
            board_distribution['深证主板'] = main_count
            board_distribution['创业板'] = gem_count
        elif exchange == 'BJ':
            board_distribution['北交所'] = count
        else:
            board_distribution['其他'] = board_distribution.get('其他', 0) + count

    return {
        "statistics": {
            "total_stocks": total_stocks,
            "today_stocks": today_stocks,
            "total_daily_data": total_daily,
            "today_data": today_sync,
            "watchlist_count": watchlist_count,
            "today_sync_count": today_sync,
            "board_distribution": board_distribution,
            "last_update": datetime.now().isoformat()
        }
    }


@router.get("/realtime/all")
async def get_all_realtime_quotes(limit: int = 100):
    """获取所有股票实时行情"""
    from app.data_providers.stock_data import DataProviderManager
    
    try:
        manager = DataProviderManager()
        df = manager.get_realtime_quote()
        
        if df.empty:
            return {"stocks": [], "total": 0}
        
        # 限制返回数量
        df = df.head(limit)
        
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                "symbol": row.get('symbol'),
                "name": row.get('name'),
                "price": float(row.get('price', 0)) if row.get('price') else None,
                "change_pct": float(row.get('change_pct', 0)) if row.get('change_pct') else None,
                "volume": float(row.get('volume', 0)) if row.get('volume') else None,
                "amount": float(row.get('amount', 0)) if row.get('amount') else None,
            })
        
        return {"stocks": stocks, "total": len(stocks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/minute/{symbol}")
async def get_stock_minute(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    frequency: str = "5"
):
    """获取股票分钟线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        frequency: 分钟频率，可选 5, 15, 30, 60
    """
    from app.data_providers.stock_data import DataProviderManager
    
    if frequency not in ["5", "15", "30", "60"]:
        raise HTTPException(status_code=400, detail="frequency must be 5, 15, 30 or 60")
    
    try:
        manager = DataProviderManager()
        df = manager.get_stock_minute(symbol, start_date, end_date, frequency)
        
        if df.empty:
            return {"data": [], "total": 0}
        
        data = []
        for _, row in df.iterrows():
            data.append({
                "date": row.get('date'),
                "time": row.get('time'),
                "datetime": row.get('datetime').isoformat() if pd.notna(row.get('datetime')) else None,
                "open": float(row.get('open', 0)) if row.get('open') else None,
                "high": float(row.get('high', 0)) if row.get('high') else None,
                "low": float(row.get('low', 0)) if row.get('low') else None,
                "close": float(row.get('close', 0)) if row.get('close') else None,
                "volume": float(row.get('volume', 0)) if row.get('volume') else None,
                "amount": float(row.get('amount', 0)) if row.get('amount') else None,
            })
        
        return {"data": data, "total": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime/{symbol}")
async def get_realtime_quote(symbol: str):
    """获取股票实时行情"""
    from app.data_providers.stock_data import DataProviderManager
    
    try:
        manager = DataProviderManager()
        df = manager.get_realtime_quote(symbol)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        row = df.iloc[0]
        return {
            "symbol": row.get('symbol'),
            "name": row.get('name'),
            "price": float(row.get('price', 0)) if row.get('price') else None,
            "change": float(row.get('change', 0)) if row.get('change') else None,
            "change_pct": float(row.get('change_pct', 0)) if row.get('change_pct') else None,
            "open": float(row.get('open', 0)) if row.get('open') else None,
            "high": float(row.get('high', 0)) if row.get('high') else None,
            "low": float(row.get('low', 0)) if row.get('low') else None,
            "pre_close": float(row.get('pre_close', 0)) if row.get('pre_close') else None,
            "volume": float(row.get('volume', 0)) if row.get('volume') else None,
            "amount": float(row.get('amount', 0)) if row.get('amount') else None,
            "turnover_rate": float(row.get('turnover_rate', 0)) if row.get('turnover_rate') else None,
            "pe": float(row.get('pe', 0)) if row.get('pe') else None,
            "pb": float(row.get('pb', 0)) if row.get('pb') else None,
            "market_cap": float(row.get('market_cap', 0)) if row.get('market_cap') else None,
            "update_time": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection")
async def test_connection():
    """测试数据源连接状态"""
    results = {
        "akshare": True,
        "baostock": True
    }
    
    try:
        from app.data_providers.stock_data import DataProviderManager
        manager = DataProviderManager()
        
        # 测试akshare
        try:
            df = manager.akshare.get_stock_daily("000001", "20240101", "20240110")
            results["akshare"] = len(df) > 0
        except Exception:
            results["akshare"] = False
        
        # 测试baostock
        try:
            df = manager.baostock.get_stock_daily("000001", "2024-01-01", "2024-01-10")
            results["baostock"] = len(df) > 0
        except Exception:
            results["baostock"] = False
    except Exception:
        pass
    
    return {"results": results}


@router.get("/provider/status")
async def get_provider_status():
    """获取当前数据源设置"""
    from app.data_providers.stock_data import DataProviderManager
    manager = DataProviderManager()
    
    return {
        "primary": manager.primary,
        "providers": [
            {
                "name": "baostock",
                "status": "active",
                "priority": 1,
                "description": "Baostock数据源"
            },
            {
                "name": "akshare",
                "status": "active",
                "priority": 2,
                "description": "AKShare数据源"
            }
        ]
    }


@router.get("/sync/progress")
async def get_sync_progress():
    """获取最新的同步进度"""
    from app.services.sync_progress import sync_progress_manager
    
    progress = sync_progress_manager.get_latest_progress()
    if progress:
        return progress.to_dict()
    return {"status": "no_task"}


@router.get("/sync/progress/{task_id}")
async def get_sync_progress_by_id(task_id: str):
    """获取指定任务的同步进度"""
    from app.services.sync_progress import sync_progress_manager
    
    progress = sync_progress_manager.get_progress(task_id)
    if progress:
        return progress.to_dict()
    return {"status": "not_found"}


@router.post("/sync/stock-list")
async def sync_stock_list(
    background_tasks: BackgroundTasks
):
    async def sync_task():
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            count = await stock_data_service.sync_stock_list(db)
            logger.info(f"同步股票列表完成: {count} 只股票")

    background_tasks.add_task(sync_task)
    return {"status": "started", "message": "股票列表同步已开始"}


@router.post("/sync/stock-daily/{symbol}")
async def sync_stock_daily(
    symbol: str,
    days: int = 365,
    db: AsyncSession = Depends(get_db)
):
    count = await stock_data_service.sync_stock_daily(db, symbol, days=days)
    return {
        "status": "success",
        "symbol": symbol,
        "count": count,
        "message": f"同步了 {count} 条数据"
    }


@router.post("/sync/all-stocks-daily")
async def sync_all_stocks_daily(
    background_tasks: BackgroundTasks,
    days: int = 30,
    mode: str = "incremental"
):
    import uuid
    task_id = str(uuid.uuid4())
    
    if mode not in ["full", "incremental"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'full' or 'incremental'")

    async def sync_task():
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await stock_data_service.sync_all_stocks_daily(db, days, mode, task_id)
            logger.info(f"批量同步完成: {result}")

    background_tasks.add_task(sync_task)
    return {
        "status": "started",
        "task_id": task_id,
        "message": f"已开始后台同步所有股票近{days}天的数据（{mode}模式）",
        "days": days,
        "mode": mode,
        "timestamp": datetime.now()
    }


@router.post("/sync/batch-stocks-daily")
async def sync_batch_stocks_daily(
    request: BatchSyncRequest,
    background_tasks: BackgroundTasks
):
    import uuid
    task_id = str(uuid.uuid4())
    
    if request.mode not in ["full", "incremental"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'full' or 'incremental'")
    if request.scope not in ["all", "watchlist"]:
        raise HTTPException(status_code=400, detail="Invalid scope. Must be 'all' or 'watchlist'")

    async def sync_task():
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            if request.scope == "watchlist":
                result = await stock_data_service.sync_watchlist_stocks_daily(db, request.days, request.mode, task_id)
            else:
                result = await stock_data_service.sync_all_stocks_daily(db, request.days, request.mode, task_id)
            logger.info(f"后台任务完成: {result}")

    background_tasks.add_task(sync_task)
    scope_text = "自选股" if request.scope == "watchlist" else "所有股票"
    mode_text = "全新" if request.mode == "full" else "增量"
    years = request.days // 365
    if years > 0:
        period_text = f"{years}年"
    else:
        period_text = f"{request.days}天"
    return {
        "status": "started",
        "task_id": task_id,
        "message": f"已开始后台同步{scope_text}近{period_text}的数据（{mode_text}模式）",
        "days": request.days,
        "scope": request.scope,
        "mode": request.mode,
        "timestamp": datetime.now()
    }


@router.get("/stocks")
async def search_stocks(
    search: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """搜索股票列表"""
    from sqlalchemy import select, or_
    from app.models.stock import Stock
    
    query = select(Stock)
    
    if search:
        search_lower = search.lower()
        query = query.where(
            or_(
                Stock.symbol.ilike(f"%{search}%"),
                Stock.name.ilike(f"%{search}%"),
                Stock.name_pinyin.ilike(f"%{search_lower}%")
            )
        )
    
    query = query.limit(limit)
    result = await db.execute(query)
    stocks = result.scalars().all()
    
    return {
        "items": [
            {
                "id": stock.id,
                "symbol": stock.symbol,
                "name": stock.name,
                "exchange": stock.exchange,
                "industry": stock.industry,
                "is_active": stock.is_active
            }
            for stock in stocks
        ],
        "total": len(stocks)
    }


@router.get("/stock/{symbol}")
async def get_stock_info(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    stock = await stock_data_service.get_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    return {
        "id": stock.id,
        "symbol": stock.symbol,
        "name": stock.name,
        "exchange": stock.exchange,
        "industry": stock.industry,
        "list_date": stock.list_date.isoformat() if stock.list_date else None,
        "is_active": stock.is_active
    }


@router.get("/stock/{symbol}/stats")
async def get_stock_stats(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """获取股票统计信息"""
    from sqlalchemy import func, select
    from app.models.stock import Stock, StockDaily

    stock = await stock_data_service.get_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    result = await db.execute(
        select(func.count(StockDaily.id)).where(StockDaily.stock_id == stock.id)
    )
    total_count = result.scalar() or 0

    result = await db.execute(
        select(StockDaily.trade_date)
        .where(StockDaily.stock_id == stock.id)
        .order_by(StockDaily.trade_date.desc())
        .limit(1)
    )
    latest_date = result.scalar_one_or_none()

    result = await db.execute(
        select(StockDaily.trade_date)
        .where(StockDaily.stock_id == stock.id)
        .order_by(StockDaily.trade_date)
        .limit(1)
    )
    earliest_date = result.scalar_one_or_none()

    return {
        "symbol": symbol,
        "name": stock.name,
        "total_records": min(total_count, 9999),
        "actual_records": total_count,
        "latest_date": latest_date.isoformat() if latest_date else None,
        "earliest_date": earliest_date.isoformat() if earliest_date else None
    }


@router.get("/stock/{symbol}/timeline")
async def get_stock_timeline(
    symbol: str,
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取股票分时数据"""
    from sqlalchemy import select, func
    from app.models.stock import Stock
    from app.models.timeline import StockTimeline
    from datetime import datetime as dt
    
    stock = await stock_data_service.get_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # 解析日期
    if date:
        try:
            target_date = dt.strptime(date, "%Y-%m-%d").date()
        except:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = None
    
    # 查询分时数据
    query = select(StockTimeline).where(StockTimeline.stock_id == stock.id)
    
    if target_date:
        # 查询指定日期的数据
        query = query.where(
            StockTimeline.trade_date >= dt.combine(target_date, dt.min.time()),
            StockTimeline.trade_date < dt.combine(target_date, dt.max.time())
        )
    else:
        # 查询最新一天的数据
        latest_result = await db.execute(
            select(func.max(StockTimeline.trade_date)).where(StockTimeline.stock_id == stock.id)
        )
        latest = latest_result.scalar_one_or_none()
        if latest:
            query = query.where(
                StockTimeline.trade_date >= dt.combine(latest.date(), dt.min.time()),
                StockTimeline.trade_date < dt.combine(latest.date(), dt.max.time())
            )
    
    query = query.order_by(StockTimeline.trade_date)
    
    result = await db.execute(query)
    timeline_data = result.scalars().all()
    
    # 获取日期
    timeline_date = None
    if timeline_data:
        timeline_date = timeline_data[0].trade_date.strftime("%Y-%m-%d")
    
    return {
        "date": timeline_date,
        "data": [
            {
                "time": item.trade_date.strftime("%H:%M"),
                "price": float(item.price) if item.price else None,
                "volume": float(item.volume) if item.volume else None,
                "amount": float(item.amount) if item.amount else None,
                "avg_price": float(item.avg_price) if item.avg_price else None
            }
            for item in timeline_data
        ]
    }


@router.post("/sync/stock-timeline/{symbol}")
async def sync_stock_timeline(
    symbol: str,
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """同步股票分时数据"""
    from datetime import datetime as dt
    
    stock = await stock_data_service.get_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    try:
        if date:
            count = await stock_data_service.sync_stock_timeline(db, symbol, date)
        else:
            today = dt.now().strftime("%Y%m%d")
            count = await stock_data_service.sync_stock_timeline(db, symbol, today)
        
        return {"status": "success", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{symbol}/daily")
async def get_stock_daily(
    symbol: str,
    days: int = 365,
    db: AsyncSession = Depends(get_db)
):
    import math
    stock = await stock_data_service.get_stock(db, symbol, auto_sync=True)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    daily_data = await stock_data_service.get_stock_daily(db, symbol, days=days, auto_sync=True)
    
    def safe_float(val):
        if val is None:
            return None
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    
    return [
        {
            "trade_date": item.trade_date.isoformat(),
            "open": safe_float(item.open),
            "high": safe_float(item.high),
            "low": safe_float(item.low),
            "close": safe_float(item.close),
            "volume": safe_float(item.volume),
            "amount": safe_float(item.amount),
            "turnover_rate": safe_float(item.turnover_rate),
            "change_pct": safe_float(item.change_pct)
        }
        for item in daily_data
    ]


@router.get("/watchlist")
async def get_watchlist(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.stock import Stock, WatchlistItem

    result = await db.execute(
        select(WatchlistItem, Stock)
        .join(Stock, WatchlistItem.stock_id == Stock.id)
    )
    items = result.all()

    return {
        "items": [
            {
                "id": item.id,
                "stock_id": item.stock_id,
                "notes": item.notes,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "stock": {
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "exchange": stock.exchange,
                    "industry": stock.industry
                }
            }
            for item, stock in items
        ]
    }


@router.post("/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from app.models.stock import Stock, WatchlistItem

    stock = await stock_data_service.get_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    result = await db.execute(
        select(WatchlistItem).where(WatchlistItem.stock_id == stock.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {"status": "exists", "message": "股票已在自选列表中"}

    watchlist_item = WatchlistItem(stock_id=stock.id)
    db.add(watchlist_item)
    await db.commit()

    return {"status": "added", "message": "已添加到自选列表"}


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select, delete
    from app.models.stock import Stock, WatchlistItem

    stock = await stock_data_service.get_stock(db, symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    await db.execute(
        delete(WatchlistItem).where(WatchlistItem.stock_id == stock.id)
    )
    await db.commit()

    return {"status": "removed", "message": "已从自选列表移除"}
