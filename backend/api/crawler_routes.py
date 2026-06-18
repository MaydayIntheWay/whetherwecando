"""
爬虫相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from database.connection import get_pool
from asyncpg import Pool
from crawler.auth_manager import AuthManager
from crawler.media_crawler_adapter import MediaCrawlerAdapter
from crawler.task_scheduler import TaskScheduler
from crawler.data_transformer import DataTransformer
from crawler.models import (
    Platform, AuthConfigRequest, CrawlRequest,
    ApiResponse, ErrorResponse
)

router = APIRouter(prefix="/api/crawler", tags=["crawler"])


async def get_auth_manager(db_pool: Pool = Depends(get_pool)) -> AuthManager:
    return AuthManager(db_pool)


async def get_task_scheduler(db_pool: Pool = Depends(get_pool)) -> TaskScheduler:
    auth_manager = AuthManager(db_pool)
    adapter = MediaCrawlerAdapter(auth_manager)
    transformer = DataTransformer()
    return TaskScheduler(adapter, transformer, db_pool)


@router.post("/auth/config")
async def configure_auth(
    request: AuthConfigRequest,
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    try:
        result = await auth_manager.configure_cookie(request)
        return ApiResponse(
            success=True,
            data=result.model_dump()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=str(e),
                error_code="INVALID_COOKIE"
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=f"配置失败: {str(e)}",
                error_code="CONFIG_ERROR"
            ).model_dump()
        )


@router.get("/auth/qrcode/{platform}")
async def get_qrcode(
    platform: Platform,
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    try:
        result = await auth_manager.generate_qrcode(platform)
        return ApiResponse(
            success=True,
            data=result.model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=f"生成二维码失败: {str(e)}",
                error_code="QRCODE_ERROR"
            ).model_dump()
        )


@router.get("/auth/status/{platform}")
async def get_auth_status(
    platform: Platform,
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    try:
        result = await auth_manager.validate_auth(platform)
        return ApiResponse(
            success=True,
            data=result.model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=f"查询状态失败: {str(e)}",
                error_code="STATUS_ERROR"
            ).model_dump()
        )


@router.post("/crawl")
async def crawl(
    request: CrawlRequest,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    try:
        result = await task_scheduler.execute_task(
            platform=request.platform,
            keyword=request.keyword,
            max_count=request.max_count
        )
        return ApiResponse(
            success=True,
            data=result.model_dump()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=str(e),
                error_code="AUTH_EXPIRED"
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=f"爬取失败: {str(e)}",
                error_code="CRAWL_ERROR"
            ).model_dump()
        )
