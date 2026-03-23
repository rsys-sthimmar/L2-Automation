from app.db.database import engine, Base
import app.models.user  # noqa: F401
import app.models.knowledge  # noqa: F401


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
