import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine

from mybot.utils.config import Config

async def column_exists(conn, table, column):
    def check(sync_conn):
        inspector = inspect(sync_conn)
        cols = [c['name'] for c in inspector.get_columns(table)]
        return column in cols
    return await conn.run_sync(check)

async def add_column(conn, table, column_def):
    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))

async def main():
    engine = create_async_engine(Config.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        if not await column_exists(conn, 'users', 'is_vip'):
            await add_column(conn, 'users', 'is_vip BOOLEAN DEFAULT FALSE')
        if not await column_exists(conn, 'users', 'vip_last_checked'):
            await add_column(conn, 'users', 'vip_last_checked DATETIME')
    await engine.dispose()
    print('Migration completed.')

if __name__ == '__main__':
    asyncio.run(main())
