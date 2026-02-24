"""修改stock_daily表的价格字段精度"""
import asyncio
import sys
sys.path.insert(0, 'f:\\stock\\macroquant\\backend')

from sqlalchemy import text
from app.core.database import engine

async def migrate():
    async with engine.begin() as conn:
        # 修改价格字段精度为12位整数，5位小数
        await conn.execute(text("""
            ALTER TABLE stock_daily 
            ALTER COLUMN open TYPE NUMERIC(12, 5),
            ALTER COLUMN high TYPE NUMERIC(12, 5),
            ALTER COLUMN low TYPE NUMERIC(12, 5),
            ALTER COLUMN close TYPE NUMERIC(12, 5)
        """))
        print("价格字段精度已修改为 NUMERIC(12, 5)")

if __name__ == "__main__":
    asyncio.run(migrate())
