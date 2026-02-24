"""检查创业板股票数据"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_gem_stocks():
    async with engine.connect() as conn:
        # 查询300开头的股票数量
        print("=" * 60)
        print("300开头的股票（创业板）")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM stocks WHERE symbol LIKE '300%'
        """))
        count = result.scalar()
        print(f"300开头的股票总数: {count}")
        
        # 查询exchange='SZ'且symbol以300开头的股票
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM stocks WHERE exchange = 'SZ' AND symbol LIKE '300%'
        """))
        sz_gem_count = result.scalar()
        print(f"exchange='SZ'且300开头的股票: {sz_gem_count}")
        
        # 查询exchange='SZ'的所有股票
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM stocks WHERE exchange = 'SZ'
        """))
        sz_total = result.scalar()
        print(f"exchange='SZ'的所有股票: {sz_total}")
        
        # 查询300开头但exchange不是SZ的股票
        result = await conn.execute(text("""
            SELECT symbol, name, exchange FROM stocks 
            WHERE symbol LIKE '300%' AND exchange != 'SZ'
            LIMIT 10
        """))
        rows = result.fetchall()
        if rows:
            print(f"\n300开头但exchange不是SZ的股票:")
            for row in rows:
                print(f"  {row[0]} {row[1]} - exchange: {row[2]}")
        
        # 查询3开头但不是300开头的股票
        result = await conn.execute(text("""
            SELECT symbol, name, exchange FROM stocks 
            WHERE symbol LIKE '3%' AND symbol NOT LIKE '300%'
            LIMIT 20
        """))
        rows = result.fetchall()
        if rows:
            print(f"\n3开头但不是300开头的股票:")
            for row in rows:
                print(f"  {row[0]} {row[1]} - exchange: {row[2]}")

if __name__ == "__main__":
    asyncio.run(check_gem_stocks())
