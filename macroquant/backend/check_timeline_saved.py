"""检查分时数据保存情况"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_timeline():
    async with engine.connect() as conn:
        # 查询各股票的分时数据数量
        print("=" * 60)
        print("各股票分时数据统计")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT s.symbol, s.name, COUNT(st.id) as count
            FROM stocks s
            LEFT JOIN stock_timeline st ON s.id = st.stock_id
            GROUP BY s.symbol, s.name
            HAVING COUNT(st.id) > 0
            ORDER BY count DESC
            LIMIT 20
        """))
        
        rows = result.fetchall()
        print(f"\n有分时数据的股票数: {len(rows)}")
        for row in rows:
            print(f"  {row[0]} {row[1]}: {row[2]} 条")
        
        # 检查688116
        print("\n" + "=" * 60)
        print("688116 分时数据")
        print("=" * 60)
        
        result = await conn.execute(text("""
            SELECT st.trade_date, st.price, st.volume 
            FROM stock_timeline st
            JOIN stocks s ON st.stock_id = s.id
            WHERE s.symbol = '688116'
            ORDER BY st.trade_date DESC
            LIMIT 10
        """))
        
        rows = result.fetchall()
        if rows:
            print(f"688116 有 {len(rows)} 条分时数据")
            for row in rows:
                print(f"  {row[0]}: 价格={row[1]}, 成交量={row[2]}")
        else:
            print("688116 没有分时数据")

if __name__ == "__main__":
    asyncio.run(check_timeline())
