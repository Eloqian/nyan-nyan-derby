import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.db import DATABASE_URL

# Modify DATABASE_URL for asyncpg if needed, or assume app.db has the correct async url
# Typical pattern: postgresql+asyncpg://...

async def fix_database():
    print(f"Connecting to database...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Dropping column 'is_npc' from table 'player'...")
        try:
            await conn.execute(text("ALTER TABLE player DROP COLUMN is_npc"))
            print("Successfully dropped column 'is_npc'.")
        except Exception as e:
            print(f"Error (maybe column doesn't exist?): {e}")

    await engine.dispose()

if __name__ == "__main__":
    # Ensure we can import app.db
    import sys
    import os
    sys.path.append(os.getcwd())
    
    asyncio.run(fix_database())
