"""
Idea可行性验证工具 - FastAPI后端入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings, ensure_cache_dirs
from database.connection import get_pool, close_pool
from api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    ensure_cache_dirs()
    await get_pool()
    print(f"✅ 数据库连接池已初始化")
    print(f"✅ 缓存目录已创建: {settings.cookie_path}")
    
    yield
    
    await close_pool()
    print("✅ 数据库连接池已关闭")


app = FastAPI(
    title="Idea可行性验证工具",
    description="面向中文市场的自动化产品可行性验证平台",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Idea可行性验证工具 API"}


@app.get("/health")
async def health():
    """健康检查接口"""
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port
    )
