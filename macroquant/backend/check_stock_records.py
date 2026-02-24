"""检查数据库中特定股票的记录数"""
import asyncio
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.stock import Stock, StockDaily

async def check_stock_records():
    async with AsyncSessionLocal() as db:
        # 检查688212的记录数
        print("=" * 60)
        print("检查688212股票的记录数")
        print("=" * 60)

        result = await db.execute(select(Stock).where(Stock.symbol == "688212"))
        stock = result.scalar_one_or_none()

        if stock:
            print(f"\n股票信息:")
            print(f"  ID: {stock.id}")
            print(f"  代码: {stock.symbol}")
            print(f"  名称: {stock.name}")

            # 统计记录数
            result = await db.execute(
                select(func.count(StockDaily.id)).where(StockDaily.stock_id == stock.id)
            )
            count = result.scalar()
            print(f"\n  数据库中总记录数: {count}")

            # 查询日期范围
            result = await db.execute(
                select(StockDaily.trade_date)
                .where(StockDaily.stock_id == stock.id)
                .order_by(StockDaily.trade_date)
            )
            dates = result.scalars().all()
            if dates:
                print(f"  日期范围: {dates[0]} 到 {dates[-1]}")
        else:
            print("股票不存在")

        # 检查其他自选股的记录数
        print("\n" + "=" * 60)
        print("检查所有自选股的记录数")
        print("=" * 60)

        from app.models.stock import WatchlistItem
        result = await db.execute(select(WatchlistItem))
        watchlist = result.scalars().all()

        for item in watchlist:
            stock_result = await db.execute(select(Stock).where(Stock.id == item.stock_id))
            s = stock_result.scalar_one_or_none()
            if s:
                count_result = await db.execute(
                    select(func.count(StockDaily.id)).where(StockDaily.stock_id == s.id)
                )
                c = count_result.scalar()
                print(f"  {s.symbol} ({s.name}): {c} 条")

if __name__ == "__main__":
    asyncio.run(check_stock_records())
