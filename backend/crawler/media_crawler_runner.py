"""
MediaCrawler爬虫运行器 — 通过子进程调用MediaCrawler

绕过 app_runner.run() 的信号处理（Windows 上 signal.SIGTERM 不存在会导致崩溃），
改用 asyncio.run() 直接运行 main() + async_cleanup()。
"""
import asyncio
import sys
import os
import json
import random
from pathlib import Path
from typing import Optional, Callable


class MediaCrawlerRunner:
    def __init__(self):
        self.timeout = 300
        self.retry_times = 2
        self.retry_interval = 10

    async def run_crawler(
        self,
        media_crawler_dir: str,
        platform: str,
        keyword: str,
        cookie: str,
        max_count: int,
        output_dir: str,
        progress_callback: Optional[Callable] = None,
    ) -> bool:
        await self._random_delay()

        for attempt in range(self.retry_times):
            try:
                if progress_callback:
                    await progress_callback(
                        current=0,
                        total=max_count,
                        message=f"正在启动爬虫（尝试 {attempt + 1}/{self.retry_times}）...",
                    )

                result = await self._run_subprocess(
                    media_crawler_dir=media_crawler_dir,
                    platform=platform,
                    keyword=keyword,
                    cookie=cookie,
                    max_count=max_count,
                    output_dir=output_dir,
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
        media_crawler_dir: str,
        platform: str,
        keyword: str,
        cookie: str,
        max_count: int,
        output_dir: str,
    ) -> bool:
        mc_dir = os.path.abspath(media_crawler_dir)
        runner_script_path = os.path.join(output_dir, "_mc_runner.py")

        headless_bool = os.environ.get("CRAWLER_HEADLESS", "true").lower() not in ("false", "0", "no")

        with open(runner_script_path, "w", encoding="utf-8") as f:
            f.write(f'''\
import sys, os
sys.path.insert(0, {json.dumps(mc_dir)})
# 清理 argv 避免 Typer 解析垃圾参数导致 SystemExit
sys.argv = [sys.argv[0]]

import config

# 在导入任何 MediaCrawler 模块之前设置所有配置
config.PLATFORM = {json.dumps(platform)}
config.KEYWORDS = {json.dumps(keyword)}
config.LOGIN_TYPE = "cookie"
config.COOKIES = {json.dumps(cookie)}
config.CRAWLER_TYPE = "search"
config.CRAWLER_MAX_NOTES_COUNT = {max_count}
config.HEADLESS = {headless_bool}
config.ENABLE_CDP_MODE = False
config.CDP_CONNECT_EXISTING = False
config.CDP_HEADLESS = True
config.AUTO_CLOSE_BROWSER = True
config.SAVE_LOGIN_STATE = False
config.SAVE_DATA_OPTION = "jsonl"
config.SAVE_DATA_PATH = {json.dumps(output_dir)}
config.ENABLE_GET_COMMENTS = False
config.ENABLE_GET_SUB_COMMENTS = False
config.ENABLE_GET_MEIDAS = False
config.ENABLE_GET_WORDCLOUD = False
config.ENABLE_IP_PROXY = False
config.START_PAGE = 1
config.MAX_CONCURRENCY_NUM = 1

import asyncio
from main import main, async_cleanup


async def _run():
    try:
        await main()
    finally:
        await async_cleanup()


asyncio.run(_run())
''')

        process = await asyncio.create_subprocess_exec(
            sys.executable, runner_script_path,
            cwd=media_crawler_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                stdout_msg = stdout.decode("utf-8", errors="ignore")
                raise RuntimeError(
                    f"爬虫执行失败（exit={process.returncode}）：{error_msg}\\n{stdout_msg}"
                )

            return True

        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"爬虫执行超时（{self.timeout}秒）")

    async def _random_delay(self):
        delay = random.uniform(2, 5)
        await asyncio.sleep(delay)
