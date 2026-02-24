"""检查300449分时数据"""
import asyncio
from datetime import date
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models.stock import Stock, StockTimeline

async def check_timeline():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("检查300449分时数据")
        print("=" * 60)
        
        # 查询股票
        result = await db.execute(select(Stock).where(Stock.symbol == "300449"))
        stock = result.scalar_one_or_none()
        
        if not stock:
            print("股票300449不存在")
            return
        
        print(f"股票ID: {stock.id}, 名称: {stock.name}")
        
        # 查询分时数据总数
        count_result = await db.execute(
            select(func.count(StockTimeline.id)).where(StockTimeline.stock_id == stock.id)
        )
        total_count = count_result.scalar()
        print(f"\n分时数据总数: {total_count}")
        
        # 查询最新分时数据日期
        if total_count > 0:
            latest_result = await db.execute(
                select(StockTimeline.trade_date)
                .where(StockTimeline.stock_id == stock.id)
                .order_by(StockTimeline.trade_date.desc())
                .limit(1)
            )
            latest_date = latest_result.scalar_one_or_none()
            print(f"最新分时日期: {latest_date}")
            
            # 查询2026-02-12的数据
            target_date = date(2026, 2, 12)
            day_result = await db.execute(
                select(func.count(StockTimeline.id))
                .where(StockTimeline.stock_id == stock.id)
                .where(StockTimeline.trade_date >= target_date)
                .where(StockTimeline.trade_date < date(2026, 2, 13))
            )
            day_count = day_result.scalar()
            print(f"2026-02-12 分时数据: {day_count} 条")
            
            # 查询最近的分时数据
            recent_result = await db.execute(
                select(StockTimeline)
                .where(StockTimeline.stock_id == stock.id)
                .order_by(StockTimeline.trade_date.desc())
                .limit(5)
            )
            recent_data = recent_result.scalars().all()
            print(f"\n最近5条分时数据:")
            for item in recent_data:
                print(f"  {item.trade_date}: 价格={item.price}, 成交量={item.volume}")

if __name__ == "__main__":
    asyncio.run(check_timeline())
