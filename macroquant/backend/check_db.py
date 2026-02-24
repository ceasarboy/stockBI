import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_db():
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = result.fetchall()
        print("Tables:", [t[0] for t in tables])
        
        try:
            result = await conn.execute(text("SELECT id, username, role FROM users"))
            users = result.fetchall()
            print("Users:", users)
        except Exception as e:
            print(f"Error querying users: {e}")
    
    await engine.dispose()

asyncio.run(check_db())
