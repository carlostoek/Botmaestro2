import asyncio
from database.setup import init_db, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TriviaSystemConfig

async def create_trivia_tables():
    await init_db()

async def add_trivia_permissions_to_roles():
    # Placeholder for permission integration
    pass

async def create_default_trivia_config(session: AsyncSession):
    config = await session.get(TriviaSystemConfig, 1)
    if not config:
        config = TriviaSystemConfig(id=1)
        session.add(config)
        await session.commit()

async def migrate_trivia_tables():
    """Migración para agregar tablas de trivias"""
    await create_trivia_tables()
    Session = await get_session()
    async with Session() as session:
        await add_trivia_permissions_to_roles()
        await create_default_trivia_config(session)
    print("✅ Migración de trivias completada")

if __name__ == "__main__":
    asyncio.run(migrate_trivia_tables())
