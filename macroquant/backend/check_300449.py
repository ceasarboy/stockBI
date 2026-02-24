"""检查300449股票的问题"""
import asyncio
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.stock import Stock, StockDaily

async def check_stock():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("检查300449股票")
        print("=" * 60)

        # 检查股票是否存在
        result = await db.execute(select(Stock).where(Stock.symbol == "300449"))
        stock = result.scalar_one_or_none()

        if stock:
            print(f"\n股票信息:")
            print(f"  ID: {stock.id}")
            print(f"  代码: {stock.symbol}")
            print(f"  名称: {stock.name}")
            print(f"  交易所: {stock.exchange}")

            # 统计记录数
            result = await db.execute(
                select(func.count(StockDaily.id)).where(StockDaily.stock_id == stock.id)
            )
            count = result.scalar()
            print(f"  日线数据: {count} 条")

            # 检查是否有数据
            if count > 0:
                result = await db.execute(
                    select(StockDaily)
                    .where(StockDaily.stock_id == stock.id)
                    .order_by(StockDaily.trade_date.desc())
                    .limit(5)
                )
                recent_data = result.scalars().all()
                print(f"\n  最近5条数据:")
                for d in recent_data:
                    print(f"    {d.trade_date}: 开{d.open} 高{d.high} 低{d.low} 收{d.close}")
        else:
            print("\n股票不存在！")

        # 测试API
        print("\n" + "=" * 60)
        print("测试API")
        print("=" * 60)

        import requests
        try:
            response = requests.get("http://localhost:8000/api/v1/data/stock/300449")
            print(f"股票信息API: {response.status_code}")
            if response.status_code != 200:
                print(f"  错误: {response.text}")
        except Exception as e:
            print(f"  异常: {e}")

        try:
            response = requests.get("http://localhost:8000/api/v1/data/stock/300449/stats")
            print(f"统计信息API: {response.status_code}")
            if response.status_code == 200:
                print(f"  数据: {response.json()}")
            else:
                print(f"  错误: {response.text}")
        except Exception as e:
            print(f"  异常: {e}")

        try:
            response = requests.get("http://localhost:8000/api/v1/data/stock/300449/daily?days=365")
            print(f"日线数据API: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  返回数据条数: {len(data)}")
            else:
                print(f"  错误: {response.text}")
        except Exception as e:
            print(f"  异常: {e}")

if __name__ == "__main__":
    asyncio.run(check_stock())
