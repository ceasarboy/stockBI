"""检查更新后的exchange字段"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_exchange():
    async with engine.connect() as conn:
        # 查询各交易所股票数量
        print("=" * 60)
        print("各交易所股票数量")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT exchange, COUNT(*) as count
            FROM stocks
            GROUP BY exchange
            ORDER BY count DESC
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]} 只")
        
        # 查询920开头的股票
        print("\n" + "=" * 60)
        print("920开头的股票")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT symbol, name, exchange
            FROM stocks
            WHERE symbol LIKE '920%'
            LIMIT 5
        """))
        
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"  {row[0]} {row[1]} - exchange: {row[2]}")
        else:
            print("没有找到920开头的股票")

if __name__ == "__main__":
    asyncio.run(check_exchange())
