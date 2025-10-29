from typing import Annotated
from psycopg import AsyncCursor
from psycopg_pool import AsyncConnectionPool
from fastapi import Depends
from .models.user import UserInDB
from psycopg.rows import dict_row, DictRow

pool: AsyncConnectionPool | None = None

async def init_pool():
    global pool
    pool = AsyncConnectionPool(
        "postgresql://user:pass@localhost/db",
        min_size=1,
        max_size=10,
    )
    await pool.open(wait=True)

async def close_pool():
    global pool
    if pool:
        await pool.close()

async def get_cursor():
    global pool
    if pool is None:
        raise RuntimeError("Connection pool is not initialized")
    
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            try:
                yield cur
            finally:
                await cur.close()

CursorDep = Annotated[AsyncCursor[DictRow], Depends(get_cursor)]

async def get_user(username: str, cur: CursorDep) -> UserInDB | None:
    result = await cur.execute("SELECT * FROM users WHERE username = $1", username)
    row = await result.fetchone()
    if row is None:
        return None
    return UserInDB(**row)