"""
数据库连接池配置
"""
from typing import Optional
from asyncpg import Pool, create_pool
from contextlib import asynccontextmanager
from config import settings

DATABASE_URL = settings.database_url

_pool: Optional[Pool] = None


async def get_pool() -> Pool:
    """获取数据库连接池"""
    global _pool
    if _pool is None:
        _pool = await create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    return _pool


async def close_pool():
    """关闭数据库连接池"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection():
    """获取数据库连接上下文管理器"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def execute_query(query: str, *args):
    """执行查询"""
    async with get_connection() as conn:
        return await conn.execute(query, *args)


async def fetch_one(query: str, *args):
    """查询单条记录"""
    async with get_connection() as conn:
        return await conn.fetchrow(query, *args)


async def fetch_all(query: str, *args):
    """查询多条记录"""
    async with get_connection() as conn:
        return await conn.fetch(query, *args)
