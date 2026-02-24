"""修复创业板股票（301开头）"""
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def fix_gem_stocks():
    async with AsyncSessionLocal() as db:
        # 查询301开头的股票数量
        result = await db.execute(text("""
            SELECT COUNT(*) FROM stocks WHERE symbol LIKE '301%'
        """))
        count_301 = result.scalar()
        print(f"301开头的股票: {count_301}")
        
        # 更新301开头的股票为创业板
        result = await db.execute(text("""
            UPDATE stocks SET exchange = 'SZ'
            WHERE symbol LIKE '301%'
        """))
        updated = result.rowcount
        print(f"更新301开头股票: {updated} 条")
        
        await db.commit()
        
        # 重新统计创业板数量
        result = await db.execute(text("""
            SELECT COUNT(*) FROM stocks 
            WHERE symbol LIKE '300%' OR symbol LIKE '301%'
        """))
        total_gem = result.scalar()
        print(f"\n创业板总数（300+301开头）: {total_gem}")

if __name__ == "__main__":
    asyncio.run(fix_gem_stocks())
