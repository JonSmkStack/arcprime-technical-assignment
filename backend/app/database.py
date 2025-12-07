import asyncpg
from contextlib import asynccontextmanager

from app.config import settings

pool: asyncpg.Pool | None = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(settings.database_url)


async def close_db():
    global pool
    if pool:
        await pool.close()


@asynccontextmanager
async def get_connection():
    async with pool.acquire() as connection:
        yield connection


async def get_next_docket_number() -> str:
    async with get_connection() as conn:
        result = await conn.fetchval("SELECT nextval('docket_seq')")
        return f"IDF-{result:04d}"
