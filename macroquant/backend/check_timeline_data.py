"""检查stock_timeline表数据"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_timeline():
    async with engine.connect() as conn:
        # 查询表结构
        print("=" * 60)
        print("stock_timeline表结构")
        print("=" * 60)
        result = await conn.execute(text("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_name = 'stock_timeline'
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        # 查询数据总数
        result = await conn.execute(text("SELECT COUNT(*) FROM stock_timeline"))
        count = result.scalar()
        print(f"\n数据总数: {count}")
        
        # 查询300449的分时数据
        result = await conn.execute(text("""
            SELECT st.trade_date, st.price, st.volume 
            FROM stock_timeline st
            JOIN stocks s ON st.stock_id = s.id
            WHERE s.symbol = '300449'
            ORDER BY st.trade_date DESC
            LIMIT 10
        """))
        rows = result.fetchall()
        print(f"\n300449最近10条分时数据:")
        for row in rows:
            print(f"  {row[0]}: 价格={row[1]}, 成交量={row[2]}")

if __name__ == "__main__":
    asyncio.run(check_timeline())
