"""更新股票交易所字段"""
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def update_exchange():
    async with AsyncSessionLocal() as db:
        # 更新北交所股票 (920开头)
        result = await db.execute(text("""
            UPDATE stocks SET exchange = 'BJ' 
            WHERE symbol LIKE '920%' AND exchange != 'BJ'
        """))
        bj_count = result.rowcount
        print(f"更新北交所股票: {bj_count} 条")
        
        # 更新上证主板股票 (60开头，但不是688)
        result = await db.execute(text("""
            UPDATE stocks SET exchange = 'SH' 
            WHERE symbol LIKE '6%' AND symbol NOT LIKE '688%' AND exchange != 'SH'
        """))
        sh_main_count = result.rowcount
        print(f"更新上证主板股票: {sh_main_count} 条")
        
        # 更新科创板股票 (688开头)
        result = await db.execute(text("""
            UPDATE stocks SET exchange = 'SH' 
            WHERE symbol LIKE '688%' AND exchange != 'SH'
        """))
        star_count = result.rowcount
        print(f"更新科创板股票: {star_count} 条")
        
        # 更新深证主板股票 (00开头, 但不是300)
        result = await db.execute(text("""
            UPDATE stocks SET exchange = 'SZ' 
            WHERE symbol LIKE '0%' AND symbol NOT LIKE '300%' AND exchange != 'SZ'
        """))
        sz_main_count = result.rowcount
        print(f"更新深证主板股票: {sz_main_count} 条")
        
        # 更新创业板股票 (300开头)
        result = await db.execute(text("""
            UPDATE stocks SET exchange = 'SZ' 
            WHERE symbol LIKE '300%' AND exchange != 'SZ'
        """))
        gem_count = result.rowcount
        print(f"更新创业板股票: {gem_count} 条")
        
        await db.commit()
        print("\n更新完成!")

if __name__ == "__main__":
    asyncio.run(update_exchange())
