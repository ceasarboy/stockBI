import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
from sqlalchemy import select, func

async def check_pinyin():
    async with AsyncSessionLocal() as db:
        # 检查总股票数
        result = await db.execute(select(func.count(Stock.id)))
        total = result.scalar()
        print(f"Total stocks: {total}")
        
        # 检查有拼音的股票数
        result = await db.execute(
            select(func.count(Stock.id)).where(Stock.name_pinyin != None)
        )
        with_pinyin = result.scalar()
        print(f"Stocks with pinyin: {with_pinyin}")
        
        # 显示几个示例
        result = await db.execute(
            select(Stock).where(Stock.name_pinyin != None).limit(5)
        )
        stocks = result.scalars().all()
        print("\nSample stocks with pinyin:")
        for stock in stocks:
            print(f"  {stock.symbol}: {stock.name} -> {stock.name_pinyin}")

if __name__ == "__main__":
    asyncio.run(check_pinyin())
