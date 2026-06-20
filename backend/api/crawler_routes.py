"""
爬虫相关API路由
"""
import asyncio
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


@router.get("/auth/configs")
async def get_auth_configs(
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """获取所有平台的配置摘要（不含原始 cookie）"""
    try:
        configs = await auth_manager.get_all_configs()
        return ApiResponse(
            success=True,
            data=configs
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=f"查询配置失败: {str(e)}",
                error_code="CONFIGS_ERROR"
            ).model_dump()
        )


@router.post("/crawl")
async def crawl(
    request: CrawlRequest,
    task_scheduler: TaskScheduler = Depends(get_task_scheduler)
):
    """启动爬取任务（异步，立即返回 task_id）"""
    import uuid as _uuid
    task_id = str(_uuid.uuid4())

    async def _run():
        try:
            await task_scheduler.execute_task_with_id(
                task_id=task_id,
                platform=request.platform,
                keyword=request.keyword,
                max_count=request.max_count,
            )
        except Exception as e:
            print(f"[CRAWL_TASK] 失败: {e}", flush=True)

    asyncio.create_task(_run())
    print(f"[CRAWL_TASK] 任务已启动: {task_id} ({request.platform.value} / {request.keyword})", flush=True)

    return ApiResponse(
        success=True,
        data={"task_id": task_id, "status": "running"}
    )


@router.get("/crawl/{task_id}")
async def get_crawl_result(task_id: str):
    """查询爬取任务状态和结果"""
    from database.connection import fetch_one, fetch_all
    task = await fetch_one(
        "SELECT id, platform, keyword, status, total_count, success_count, error_count, error_message FROM crawl_task WHERE id = $1",
        task_id,
    )
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = {
        "task_id": task["id"],
        "platform": task["platform"],
        "keyword": task["keyword"],
        "status": task["status"],
        "total": task["total_count"] or 0,
        "success": task["success_count"] or 0,
        "error_count": task["error_count"] or 0,
        "error_message": task["error_message"],
    }

    if task["status"] == "completed":
        items = await fetch_all(
            "SELECT platform, content, source_url, engagement, emotion_intensity FROM crawl_results WHERE crawl_task_id = $1",
            task_id,
        )
        result["items"] = [dict(row) for row in items]

    return ApiResponse(success=True, data=result)
