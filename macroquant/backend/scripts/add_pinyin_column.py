"""添加name_pinyin字段到stocks表"""
import asyncio
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def add_pinyin_column():
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # 检查字段是否已存在
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stocks' AND column_name = 'name_pinyin'
        """))
        
        if result.fetchone():
            print("Column name_pinyin already exists")
            return
        
        # 添加字段
        await conn.execute(text("""
            ALTER TABLE stocks 
            ADD COLUMN name_pinyin VARCHAR(100)
        """))
        
        # 创建索引
        await conn.execute(text("""
            CREATE INDEX idx_stocks_name_pinyin ON stocks(name_pinyin)
        """))
        
        print("Column name_pinyin added successfully")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_pinyin_column())
