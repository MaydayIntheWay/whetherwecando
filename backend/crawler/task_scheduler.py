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
    
    async def execute_task(
        self,
        platform: Platform,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> CrawlResult:
        task_id = str(uuid4())
        
        async with self._semaphore:
            await self._create_task_record(task_id, platform, keyword, max_count)
            
            try:
                await self._update_task_status(task_id, TaskStatus.RUNNING)
                
                raw_data_list = await self._retry_with_backoff(
                    self.adapter.crawl,
                    platform,
                    keyword,
                    max_count,
                    progress_callback
                )
                
                cleaned_items = self.transformer.transform_batch(
                    raw_data_list,
                    platform.value
                )
                
                valid_items = [item for item in cleaned_items if item.source_url]
                
                await self._save_results(task_id, valid_items)
                
                await self._update_task_completion(
                    task_id,
                    TaskStatus.COMPLETED,
                    len(raw_data_list),
                    len(valid_items),
                    0
                )
                
                return CrawlResult(
                    task_id=task_id,
                    platform=platform,
                    keyword=keyword,
                    total=len(raw_data_list),
                    success=len(valid_items),
                    items=[item.model_dump() for item in valid_items],
                    status=TaskStatus.COMPLETED
                )
                
            except Exception as e:
                error_message = str(e)
                await self._update_task_completion(
                    task_id,
                    TaskStatus.FAILED,
                    0,
                    0,
                    1,
                    error_message
                )
                
                await self._log_error(task_id, error_message)
                
                return CrawlResult(
                    task_id=task_id,
                    platform=platform,
                    keyword=keyword,
                    total=0,
                    success=0,
                    items=[],
                    status=TaskStatus.FAILED,
                    error_message=error_message
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
    
    async def _save_results(self, task_id: str, items: list[CleanedItem]):
        query = """
        INSERT INTO crawl_results
            (task_id, platform, keyword, content, source_url, 
             engagement, emotion_intensity, crawl_task_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        async with self.db_pool.acquire() as conn:
            for item in items:
                await conn.execute(
                    query,
                    str(uuid4()),
                    item.platform,
                    '',
                    item.content,
                    item.source_url,
                    item.engagement,
                    item.emotion_intensity,
                    task_id
                )
    
    async def _log_error(self, task_id: str, error_message: str):
        query = """
        INSERT INTO crawl_log (task_id, level, message)
        VALUES ($1, $2, $3)
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                query,
                task_id,
                'error',
                error_message
            )
