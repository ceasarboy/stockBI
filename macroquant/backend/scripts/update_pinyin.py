"""为现有股票生成拼音数据"""
import asyncio
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
from pypinyin import lazy_pinyin


def get_pinyin_initials(name: str) -> str:
    """获取股票名称的拼音首字母"""
    try:
        pinyin_list = lazy_pinyin(name)
        initials = ''.join([p[0] for p in pinyin_list if p])
        return initials.lower()
    except Exception as e:
        print(f"Error getting pinyin for {name}: {e}")
        return ""


async def update_pinyin():
    async with AsyncSessionLocal() as db:
        # 获取所有没有拼音的股票
        result = await db.execute(
            select(Stock).where(Stock.name_pinyin == None)
        )
        stocks = result.scalars().all()
        
        print(f"Found {len(stocks)} stocks without pinyin")
        
        count = 0
        for stock in stocks:
            pinyin = get_pinyin_initials(stock.name)
            if pinyin:
                stock.name_pinyin = pinyin
                count += 1
                
                # 每100条提交一次
                if count % 100 == 0:
                    await db.commit()
                    print(f"Updated {count} stocks...")
        
        # 提交剩余的数据
        await db.commit()
        print(f"Total updated: {count} stocks")
        
        # 显示几个示例
        result = await db.execute(
            select(Stock).where(Stock.name_pinyin != None).limit(10)
        )
        sample_stocks = result.scalars().all()
        print("\nSample stocks with pinyin:")
        for stock in sample_stocks:
            print(f"  {stock.symbol}: {stock.name} -> {stock.name_pinyin}")


if __name__ == "__main__":
    asyncio.run(update_pinyin())
