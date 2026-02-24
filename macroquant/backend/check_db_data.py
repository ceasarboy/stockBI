import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from app.core.database import get_db
from app.models.stock import Stock, StockDaily

async def check_db_data():
    async for db in get_db():
        result = await db.execute(
            select(Stock).where(Stock.symbol == '603533')
        )
        stock = result.scalar_one_or_none()
        if stock:
            print(f"Stock: {stock.symbol} - {stock.name}")
            
            result = await db.execute(
                select(StockDaily)
                .where(StockDaily.stock_id == stock.id)
                .order_by(StockDaily.trade_date.desc())
                .limit(20)
            )
            daily_data = result.scalars().all()
            
            print(f"\nLatest 20 records in DB:")
            for d in daily_data:
                print(f"  {d.trade_date}: O={d.open}, H={d.high}, L={d.low}, C={d.close}")
            
            result = await db.execute(
                select(StockDaily.trade_date)
                .where(StockDaily.stock_id == stock.id)
                .order_by(StockDaily.trade_date)
            )
            all_dates = [row[0] for row in result.all()]
            if all_dates:
                print(f"\nTotal records: {len(all_dates)}")
                print(f"Date range in DB: {min(all_dates)} to {max(all_dates)}")
        break

asyncio.run(check_db_data())
