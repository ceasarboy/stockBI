import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def fix_user_role():
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.connect() as conn:
        await conn.execute(text("UPDATE users SET role = 'admin' WHERE username = 'admin'"))
        await conn.commit()
        print("Fixed user role")
        
        result = await conn.execute(text("SELECT id, username, role FROM users"))
        users = result.fetchall()
        print("Users:", users)
    
    await engine.dispose()

asyncio.run(fix_user_role())
