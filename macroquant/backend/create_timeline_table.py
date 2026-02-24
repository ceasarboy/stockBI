"""创建stock_timeline表"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def create_timeline_table():
    async with engine.begin() as conn:
        # 检查表是否存在
        result = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'stock_timeline'
        """))
        exists = result.fetchone()
        
        if exists:
            print("stock_timeline表已存在")
        else:
            # 创建表
            await conn.execute(text("""
                CREATE TABLE stock_timeline (
                    id SERIAL PRIMARY KEY,
                    stock_id INTEGER NOT NULL REFERENCES stocks(id),
                    trade_date TIMESTAMP NOT NULL,
                    price NUMERIC(10, 4),
                    volume NUMERIC(20, 2),
                    amount NUMERIC(20, 2),
                    avg_price NUMERIC(10, 4)
                )
            """))
            # 创建索引
            await conn.execute(text("""
                CREATE INDEX idx_timeline_stock_date ON stock_timeline(stock_id, trade_date)
            """))
            print("stock_timeline表创建成功")

if __name__ == "__main__":
    asyncio.run(create_timeline_table())
