"""
MediaCrawler爬虫运行器
"""
import asyncio
import sys
import os
import random
from pathlib import Path
from typing import Optional, Callable
import subprocess


class MediaCrawlerRunner:
    def __init__(self):
        self.timeout = 120
        self.retry_times = 3
        self.retry_interval = 10
    
    async def run_crawler(
        self,
        config_path: str,
        media_crawler_dir: str,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        await self._random_delay()
        
        for attempt in range(self.retry_times):
            try:
                if progress_callback:
                    await progress_callback(
                        current=0,
                        total=0,
                        message=f"正在启动爬虫（尝试 {attempt + 1}/{self.retry_times}）..."
                    )
                
                result = await self._run_subprocess(
                    config_path=config_path,
                    media_crawler_dir=media_crawler_dir
                )
                
                if result:
                    return True
                
            except Exception as e:
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_interval)
                else:
                    raise RuntimeError(f"爬虫运行失败（已重试{self.retry_times}次）：{str(e)}")
        
        return False
    
    async def _run_subprocess(
        self,
        config_path: str,
        media_crawler_dir: str
    ) -> bool:
        env = os.environ.copy()
        env['MEDIA_CRAWLER_CONFIG'] = config_path
        
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "main.py",
            cwd=media_crawler_dir,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            if process.returncode == 0:
                return True
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                raise RuntimeError(f"爬虫执行失败：{error_msg}")
                
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"爬虫执行超时（{self.timeout}秒）")
    
    async def _random_delay(self):
        delay = random.uniform(2, 5)
        await asyncio.sleep(delay)


crawler_runner = MediaCrawlerRunner()
