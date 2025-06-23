import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from mybot.utils.config import Config
from mybot.database.models import User


async def main() -> None:
    """Drop the existing users table and recreate it."""
    engine = create_async_engine(Config.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # Drop only the users table to preserve other data
        await conn.execute(text("DROP TABLE IF EXISTS users"))
        # Recreate the table using the current model definition
        await conn.run_sync(User.__table__.create)
    await engine.dispose()
    print("Users table recreated.")


if __name__ == "__main__":
    asyncio.run(main())
