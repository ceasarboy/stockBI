"""检查北交所股票"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_bj_stocks():
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
        print("920开头的股票（北交所）")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT symbol, name, exchange
            FROM stocks
            WHERE symbol LIKE '920%'
            LIMIT 10
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"找到 {len(rows)} 只920开头的股票:")
            for row in rows:
                print(f"  {row[0]} {row[1]} - exchange: {row[2]}")
        else:
            print("没有找到920开头的股票")
        
        # 查询BJ交易所的股票
        print("\n" + "=" * 60)
        print("exchange='BJ'的股票")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT symbol, name, exchange
            FROM stocks
            WHERE exchange = 'BJ'
            LIMIT 10
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"找到 {len(rows)} 只BJ交易所股票:")
            for row in rows:
                print(f"  {row[0]} {row[1]}")
        else:
            print("没有找到exchange='BJ'的股票")

if __name__ == "__main__":
    asyncio.run(check_bj_stocks())
