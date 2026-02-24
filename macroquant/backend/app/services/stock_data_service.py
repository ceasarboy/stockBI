import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import joinedload

from app.models.stock import Stock, StockDaily, WatchlistItem
from app.core.config import settings
from app.data_providers.stock_data import DataProviderManager

logger = logging.getLogger(__name__)


class StockDataService:
    def __init__(self):
        self.provider = DataProviderManager()

    async def get_stocks(self, db: AsyncSession, skip: int = 0, limit: int = 100, auto_sync: bool = False) -> List[Stock]:
        result = await db.execute(select(Stock).offset(skip).limit(limit))
        stocks = result.scalars().all()
        
        if not stocks and auto_sync:
            await self.sync_stock_list(db)
            result = await db.execute(select(Stock).offset(skip).limit(limit))
            stocks = result.scalars().all()
        
        return stocks

    async def get_stock(self, db: AsyncSession, symbol: str, auto_sync: bool = False) -> Optional[Stock]:
        result = await db.execute(select(Stock).where(Stock.symbol == symbol))
        stock = result.scalar_one_or_none()
        
        if not stock and auto_sync:
            await self.sync_stock_list(db)
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = result.scalar_one_or_none()
        
        return stock

    async def get_stock_daily(self, db: AsyncSession, symbol: str, days: int = 30, auto_sync: bool = False) -> List[StockDaily]:
        stock = await self.get_stock(db, symbol, auto_sync=auto_sync)
        if not stock:
            return []
        
        result = await db.execute(
            select(StockDaily)
            .where(StockDaily.stock_id == stock.id)
            .order_by(StockDaily.trade_date.desc())
            .limit(days)
        )
        daily_data = result.scalars().all()
        
        if not daily_data and auto_sync:
            await self.sync_stock_daily(db, symbol, days=days)
            result = await db.execute(
                select(StockDaily)
                .where(StockDaily.stock_id == stock.id)
                .order_by(StockDaily.trade_date.desc())
                .limit(days)
            )
            daily_data = result.scalars().all()
        
        return daily_data

    def _get_pinyin_initials(self, name: str) -> str:
        """获取股票名称的拼音首字母"""
        try:
            from pypinyin import lazy_pinyin
            pinyin_list = lazy_pinyin(name)
            initials = ''.join([p[0] for p in pinyin_list if p])
            return initials.lower()
        except Exception as e:
            logger.error(f"Error getting pinyin for {name}: {e}")
            return ""

    async def sync_stock_list(self, db: AsyncSession) -> int:
        df = self.provider.get_stock_list()
        count = 0
        for _, row in df.iterrows():
            try:
                result = await db.execute(select(Stock).where(Stock.symbol == row['symbol']))
                stock = result.scalar_one_or_none()
                if not stock:
                    stock = Stock(
                        symbol=row['symbol'],
                        name=row['name'],
                        name_pinyin=self._get_pinyin_initials(row['name']),
                        exchange=row.get('exchange', ''),
                        industry=row.get('industry', ''),
                        list_date=row.get('list_date'),
                        is_active=True
                    )
                    db.add(stock)
                    count += 1
            except Exception as e:
                logger.error(f"Error adding stock {row.get('symbol')}: {e}")
        
        await db.commit()
        logger.info(f"Synced {count} stocks")
        return count

    def _get_sync_dates(self, days: int = 30, end_date: str = None, start_date: str = None) -> tuple:
        """获取同步日期范围
        
        由于baostock/akshare数据源只提供到2024年的历史数据，
        我们使用2024-12-31作为基准日期来计算同步范围
        """
        # 使用2024-12-31作为基准日期（数据源支持的最新日期）
        base_date = datetime(2024, 12, 31)
        
        if not end_date:
            end_date = base_date.strftime('%Y%m%d')
        if not start_date:
            start_date = (base_date - timedelta(days=days)).strftime('%Y%m%d')
        
        return start_date, end_date

    async def sync_stock_daily(self, db: AsyncSession, symbol: str, start_date: str = None, end_date: str = None, days: int = 30) -> int:
        stock = await self.get_stock(db, symbol)
        if not stock:
            logger.error(f"Stock {symbol} not found")
            return 0
        
        start_date, end_date = self._get_sync_dates(days, end_date, start_date)
        
        df = self.provider.get_stock_daily(symbol, start_date, end_date)
        
        count = 0
        for _, row in df.iterrows():
            try:
                result = await db.execute(
                    select(StockDaily).where(
                        StockDaily.stock_id == stock.id,
                        StockDaily.trade_date == row['trade_date']
                    )
                )
                daily = result.scalar_one_or_none()
                
                if daily:
                    daily.open = row['open']
                    daily.high = row['high']
                    daily.low = row['low']
                    daily.close = row['close']
                    daily.volume = row.get('volume')
                    daily.amount = row.get('amount')
                else:
                    daily = StockDaily(
                        stock_id=stock.id,
                        trade_date=row['trade_date'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row.get('volume'),
                        amount=row.get('amount')
                    )
                    db.add(daily)
                count += 1
            except Exception as e:
                logger.error(f"Error adding daily data for {symbol}: {e}")
        
        await db.commit()
        logger.info(f"Synced {count} daily records for {symbol}")
        return count

    async def sync_stock_daily_incremental(self, db: AsyncSession, symbol: str, days: int = 30) -> int:
        stock = await self.get_stock(db, symbol)
        if not stock:
            logger.error(f"Stock {symbol} not found")
            return 0
        
        result = await db.execute(
            select(StockDaily.trade_date)
            .where(StockDaily.stock_id == stock.id)
            .order_by(StockDaily.trade_date.desc())
            .limit(1)
        )
        last_date = result.scalar_one_or_none()
        
        # 使用2024-12-31作为基准日期
        base_date = datetime(2024, 12, 31)
        end_date = base_date.strftime('%Y%m%d')
        
        if last_date:
            start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
            if start_date > end_date:
                logger.info(f"Stock {symbol} is up to date")
                return 0
        else:
            start_date = (base_date - timedelta(days=days)).strftime('%Y%m%d')
        
        return await self.sync_stock_daily(db, symbol, start_date, end_date)

    async def sync_all_stocks_daily_full(self, db: AsyncSession, days: int = 30, task_id: str = None) -> Dict:
        from app.services.sync_progress import sync_progress_manager
        import uuid
        
        if not task_id:
            task_id = str(uuid.uuid4())
        
        result = await db.execute(select(Stock))
        stocks = result.scalars().all()

        results = {}
        total_stocks = len(stocks)
        # 使用2024-12-31作为基准日期
        start_date, end_date = self._get_sync_dates(days)
        
        # 创建进度
        sync_progress_manager.create_progress(task_id, "all", "full", total_stocks)
        sync_progress_manager.add_log(task_id, f"开始同步所有股票，共 {total_stocks} 只")

        for idx, stock in enumerate(stocks):
            logger.info(f"Syncing stock {stock.symbol} ({idx + 1}/{total_stocks})")
            
            # 更新进度
            sync_progress_manager.update_progress(
                task_id,
                current_stock=stock.symbol,
                current_stock_name=stock.name or stock.symbol,
                synced_stocks=idx
            )
            sync_progress_manager.add_log(task_id, f"正在同步 {stock.symbol} ({stock.name or ''})")
            
            try:
                count = await self.sync_stock_daily(db, stock.symbol, start_date, end_date)
                results[stock.symbol] = count
                
                # 更新已同步记录数
                progress = sync_progress_manager.get_progress(task_id)
                if progress:
                    sync_progress_manager.update_progress(task_id, synced_records=progress.synced_records + count)
                    
                if count > 0:
                    sync_progress_manager.add_log(task_id, f"✓ {stock.symbol} 同步 {count} 条")
            except Exception as e:
                sync_progress_manager.add_log(task_id, f"✗ {stock.symbol} 同步失败: {str(e)}")
                results[stock.symbol] = 0

        sync_progress_manager.complete_progress(task_id)
        sync_progress_manager.add_log(task_id, f"同步完成，共处理 {total_stocks} 只股票")

        return results

    async def sync_all_stocks_daily_incremental(self, db: AsyncSession, days: int = 30, task_id: str = None) -> Dict:
        from app.services.sync_progress import sync_progress_manager
        import uuid
        
        if not task_id:
            task_id = str(uuid.uuid4())
        
        result = await db.execute(select(Stock))
        stocks = result.scalars().all()
        
        results = {}
        total_stocks = len(stocks)
        
        # 创建进度
        sync_progress_manager.create_progress(task_id, "all", "incremental", total_stocks)
        sync_progress_manager.add_log(task_id, f"开始增量同步所有股票，共 {total_stocks} 只")
        
        for idx, stock in enumerate(stocks):
            logger.info(f"Checking stock {stock.symbol} ({idx + 1}/{total_stocks})")
            
            # 更新进度
            sync_progress_manager.update_progress(
                task_id,
                current_stock=stock.symbol,
                current_stock_name=stock.name or stock.symbol,
                synced_stocks=idx
            )
            sync_progress_manager.add_log(task_id, f"正在检查 {stock.symbol} ({stock.name or ''})")
            
            try:
                count = await self.sync_stock_daily_incremental(db, stock.symbol, days)
                results[stock.symbol] = {
                    'count': count,
                    'synced': count > 0
                }
                
                if count > 0:
                    progress = sync_progress_manager.get_progress(task_id)
                    if progress:
                        sync_progress_manager.update_progress(task_id, synced_records=progress.synced_records + count)
                    sync_progress_manager.add_log(task_id, f"✓ {stock.symbol} 增量同步 {count} 条")
            except Exception as e:
                sync_progress_manager.add_log(task_id, f"✗ {stock.symbol} 同步失败: {str(e)}")
                results[stock.symbol] = {'count': 0, 'synced': False}
        
        return results

    async def sync_all_stocks_daily(self, db: AsyncSession, days: int = 30, mode: str = 'full', task_id: str = None) -> Dict:
        if mode == 'full':
            results = await self.sync_all_stocks_daily_full(db, days, task_id)
            total_count = sum(results.values())
            return {
                'mode': 'full',
                'total_stocks': len(results),
                'total_records': total_count,
                'results': results
            }
        else:
            results = await self.sync_all_stocks_daily_incremental(db, days, task_id)
            synced_stocks = [k for k, v in results.items() if v['synced']]
            total_count = sum(v['count'] for v in results.values())
            return {
                'mode': 'incremental',
                'total_stocks': len(results),
                'synced_stocks': len(synced_stocks),
                'total_records': total_count,
                'results': results
            }

    async def get_watchlist(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[WatchlistItem]:
        result = await db.execute(
            select(WatchlistItem)
            .options(joinedload(WatchlistItem.stock))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def add_to_watchlist(self, db: AsyncSession, symbol: str) -> Optional[WatchlistItem]:
        stock = await self.get_stock(db, symbol)
        if not stock:
            return None
        
        result = await db.execute(
            select(WatchlistItem).where(WatchlistItem.stock_id == stock.id)
        )
        if result.scalar_one_or_none():
            return None
        
        watchlist_item = WatchlistItem(stock_id=stock.id)
        db.add(watchlist_item)
        await db.commit()
        await db.refresh(watchlist_item)
        return watchlist_item

    async def remove_from_watchlist(self, db: AsyncSession, item_id: int) -> bool:
        result = await db.execute(
            select(WatchlistItem).where(WatchlistItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if item:
            await db.delete(item)
            await db.commit()
            return True
        return False

    async def sync_watchlist_stocks_daily(self, db: AsyncSession, days: int = 30, mode: str = 'full', task_id: str = None) -> Dict:
        from app.models.stock import WatchlistItem
        from app.services.sync_progress import sync_progress_manager
        import uuid
        
        if not task_id:
            task_id = str(uuid.uuid4())
        
        result = await db.execute(select(WatchlistItem))
        watchlist = result.scalars().all()
        stocks = []
        for item in watchlist:
            stock_result = await db.execute(select(Stock).where(Stock.id == item.stock_id))
            stock = stock_result.scalar_one_or_none()
            if stock:
                stocks.append(stock)

        results = {}
        total_stocks = len(stocks)
        # 使用2024-12-31作为基准日期
        start_date, end_date = self._get_sync_dates(days)
        
        # 创建进度
        sync_progress_manager.create_progress(task_id, "watchlist", mode, total_stocks)
        sync_progress_manager.add_log(task_id, f"开始同步自选股，共 {total_stocks} 只")

        for idx, stock in enumerate(stocks):
            logger.info(f"Syncing watchlist stock {stock.symbol} ({idx + 1}/{total_stocks})")
            
            # 更新进度
            sync_progress_manager.update_progress(
                task_id,
                current_stock=stock.symbol,
                current_stock_name=stock.name or stock.symbol,
                synced_stocks=idx
            )
            sync_progress_manager.add_log(task_id, f"正在同步 {stock.symbol} ({stock.name or ''})")
            
            try:
                if mode == 'full':
                    count = await self.sync_stock_daily(db, stock.symbol, start_date, end_date)
                else:
                    count = await self.sync_stock_daily_incremental(db, stock.symbol, days)
                results[stock.symbol] = count
                
                # 更新已同步记录数
                progress = sync_progress_manager.get_progress(task_id)
                if progress:
                    sync_progress_manager.update_progress(task_id, synced_records=progress.synced_records + count)
                    
                if count > 0:
                    sync_progress_manager.add_log(task_id, f"✓ {stock.symbol} 同步 {count} 条")
            except Exception as e:
                sync_progress_manager.add_log(task_id, f"✗ {stock.symbol} 同步失败: {str(e)}")
                results[stock.symbol] = 0

        sync_progress_manager.complete_progress(task_id)
        sync_progress_manager.add_log(task_id, f"同步完成，共处理 {total_stocks} 只股票")
        
        total_count = sum(results.values())
        return {
            'mode': mode,
            'scope': 'watchlist',
            'total_stocks': len(results),
            'total_records': total_count,
            'results': results
        }

    async def sync_stock_timeline(self, db: AsyncSession, symbol: str, date_str: str) -> int:
        """同步股票分时数据"""
        from app.models.timeline import StockTimeline
        
        stock = await self.get_stock(db, symbol)
        if not stock:
            logger.error(f"Stock {symbol} not found")
            return 0
        
        try:
            import akshare as ak
            df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", start_date=f"{date_str}0930", end_date=f"{date_str}1500")
            if df.empty:
                logger.warning(f"No timeline data for {symbol} on {date_str}")
                return 0
            
            date_obj = datetime.strptime(date_str, '%Y%m%d').date()
            
            # 删除旧数据
            await db.execute(
                delete(StockTimeline).where(
                    StockTimeline.stock_id == stock.id,
                    func.date(StockTimeline.trade_date) == date_obj
                )
            )
            
            count = 0
            for _, row in df.iterrows():
                try:
                    # 转换时间字符串为datetime对象
                    time_str = str(row['时间'])
                    if len(time_str) == 8:  # 格式: HH:MM:SS
                        trade_datetime = datetime.combine(date_obj, datetime.strptime(time_str, '%H:%M:%S').time())
                    elif len(time_str) == 19:  # 格式: YYYY-MM-DD HH:MM:SS
                        trade_datetime = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        # 尝试其他格式
                        trade_datetime = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    
                    timeline = StockTimeline(
                        stock_id=stock.id,
                        trade_date=trade_datetime,
                        price=row['收盘'],
                        volume=row['成交量'],
                        amount=row['成交额'],
                        avg_price=row.get('均价')
                    )
                    db.add(timeline)
                    count += 1
                except Exception as e:
                    logger.error(f"Error adding timeline data: {e}")
            
            await db.commit()
            logger.info(f"Synced {count} timeline records for {symbol} on {date_str}")
            return count
        except Exception as e:
            logger.error(f"Error syncing timeline for {symbol}: {e}")
            return 0

    async def get_stock_timeline(self, db: AsyncSession, symbol: str, date_str: str) -> List:
        """获取股票分时数据
        
        逻辑：
        1. 先尝试获取指定日期的分时数据
        2. 如果没有，查询日线数据的最后一天，返回那天的分时数据
        """
        from app.models.timeline import StockTimeline
        from app.models.stock import StockDaily
        
        stock = await self.get_stock(db, symbol)
        if not stock:
            return []
        
        # 尝试获取指定日期的数据
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        result = await db.execute(
            select(StockTimeline)
            .where(
                StockTimeline.stock_id == stock.id,
                func.date(StockTimeline.trade_date) == date_obj
            )
            .order_by(StockTimeline.trade_date)
        )
        timeline_data = result.scalars().all()
        
        # 如果当天没有分时数据，查询日线数据的最后一天
        if not timeline_data:
            result = await db.execute(
                select(StockDaily.trade_date)
                .where(StockDaily.stock_id == stock.id)
                .order_by(StockDaily.trade_date.desc())
                .limit(1)
            )
            last_daily_date = result.scalar_one_or_none()
            
            if last_daily_date:
                result = await db.execute(
                    select(StockTimeline)
                    .where(
                        StockTimeline.stock_id == stock.id,
                        func.date(StockTimeline.trade_date) == last_daily_date
                    )
                    .order_by(StockTimeline.trade_date)
                )
                timeline_data = result.scalars().all()
        
        return timeline_data


# 创建全局实例
stock_data_service = StockDataService()
