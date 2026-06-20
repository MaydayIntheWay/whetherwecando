"""
任务调度器
"""
import asyncio
from datetime import datetime
from typing import Optional, Callable
from uuid import uuid4
from asyncpg import Pool
from models.schemas import CleanedItem
from .media_crawler_adapter import MediaCrawlerAdapter
from .data_transformer import DataTransformer
from .models import Platform, TaskStatus, CrawlResult


class TaskScheduler:
    def __init__(
        self,
        adapter: MediaCrawlerAdapter,
        transformer: DataTransformer,
        db_pool: Pool,
        max_concurrent: int = 3,
        retry_times: int = 3
    ):
        self.adapter = adapter
        self.transformer = transformer
        self.db_pool = db_pool
        self.max_concurrent = max_concurrent
        self.retry_times = retry_times
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_task_with_id(
        self,
        task_id: str,
        platform: Platform,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ):
        """异步执行爬取任务（使用指定的 task_id，结果写入 DB）"""
        async with self._semaphore:
            await self._create_task_record(task_id, platform, keyword, max_count)

            try:
                await self._update_task_status(task_id, TaskStatus.RUNNING)
                await self._log_info(task_id, f"开始爬取 {platform.value} / {keyword}")
                print(f"[SCHEDULER] 开始: {platform.value} / {keyword}", flush=True)

                platform_code = "xhs" if platform == Platform.XIAOHONGSHU else "zhihu"
                platform_name = platform.value

                success_count = 0
                total_count = 0
                async for item_dict in self.adapter.crawl_stream(
                    platform_code=platform_code,
                    platform_name=platform_name,
                    keyword=keyword,
                    max_count=max_count,
                ):
                    total_count += 1
                    try:
                        item = CleanedItem(**item_dict)
                        if item.source_url:
                            await self._save_single_result(task_id, keyword, item)
                            success_count += 1
                            print(f"  [{success_count}/{total_count}] {item.content[:80]}...", flush=True)
                            await self._update_task_progress(task_id, total_count, success_count)
                    except Exception as e:
                        print(f"  [SCHEDULER] DB写入失败 #{total_count}: {e}", flush=True)

                await self._update_task_completion(
                    task_id,
                    TaskStatus.COMPLETED,
                    total_count,
                    success_count,
                    0
                )

                msg = f"完成: {success_count}/{total_count} 条 {platform.value} 结果 (关键词: {keyword})"
                await self._log_info(task_id, msg)
                print(f"[SCHEDULER] {msg}", flush=True)

            except Exception as e:
                error_message = str(e)
                msg = f"failed: {platform.value} / {keyword}: {error_message}"
                print(f"[SCHEDULER] {msg}", flush=True)
                await self._log_error(task_id, msg)
                await self._update_task_completion(
                    task_id,
                    TaskStatus.FAILED,
                    0,
                    0,
                    1,
                    error_message
                )

    async def execute_task(
        self,
        platform: Platform,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> CrawlResult:
        task_id = str(uuid4())
        await self.execute_task_with_id(task_id, platform, keyword, max_count, progress_callback)

        # Query results from DB
        from database.connection import fetch_one, fetch_all
        task = await fetch_one(
            "SELECT * FROM crawl_task WHERE id = $1", task_id
        )
        items = await fetch_all(
            "SELECT * FROM crawl_results WHERE crawl_task_id = $1", task_id
        )
        return CrawlResult(
            task_id=task_id,
            platform=platform,
            keyword=keyword,
            total=task["total_count"] or 0 if task else 0,
            success=task["success_count"] or 0 if task else 0,
            items=[dict(row) for row in (items or [])],
            status=TaskStatus(task["status"]) if task else TaskStatus.FAILED,
        )
    
    async def _retry_with_backoff(
        self,
        func,
        *args,
        **kwargs
    ):
        last_error = None
        
        for attempt in range(self.retry_times):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.retry_times - 1:
                    wait_time = 2 ** (attempt + 1)
                    await asyncio.sleep(wait_time)
        
        raise last_error
    
    async def _create_task_record(
        self,
        task_id: str,
        platform: Platform,
        keyword: str,
        max_count: int
    ):
        query = """
        INSERT INTO crawl_task 
            (id, platform, keyword, max_count, status, started_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                query,
                task_id,
                platform.value,
                keyword,
                max_count,
                TaskStatus.RUNNING.value,
                datetime.now()
            )
    
    async def _update_task_status(self, task_id: str, status: TaskStatus):
        query = """
        UPDATE crawl_task
        SET status = $1, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, status.value, task_id)
    
    async def _update_task_completion(
        self,
        task_id: str,
        status: TaskStatus,
        total_count: int,
        success_count: int,
        error_count: int,
        error_message: Optional[str] = None
    ):
        query = """
        UPDATE crawl_task
        SET status = $1,
            total_count = $2,
            success_count = $3,
            error_count = $4,
            error_message = $5,
            completed_at = $6,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $7
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                query,
                status.value,
                total_count,
                success_count,
                error_count,
                error_message,
                datetime.now(),
                task_id
            )
    
    async def _save_single_result(self, task_id: str, keyword: str, item: CleanedItem):
        query = """
        INSERT INTO crawl_results
            (platform, keyword, content, source_url,
             engagement, crawl_task_id, crawled_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                query,
                item.platform,
                keyword,
                item.content[:500],
                item.source_url,
                item.engagement,
                task_id
            )

    async def _update_task_progress(self, task_id: str, total: int, success: int):
        query = """
        UPDATE crawl_task
        SET total_count = $1, success_count = $2, updated_at = CURRENT_TIMESTAMP
        WHERE id = $3
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, total, success, task_id)
    
    async def _log_info(self, task_id: str, message: str):
        query = """
        INSERT INTO crawl_log (task_id, level, message)
        VALUES ($1, $2, $3)
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, task_id, 'info', message)

    async def _log_error(self, task_id: str, error_message: str):
        query = """
        INSERT INTO crawl_log (task_id, level, message)
        VALUES ($1, $2, $3)
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, task_id, 'error', error_message)
