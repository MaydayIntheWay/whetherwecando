"""
MediaCrawler爬虫运行器 — 通过子进程调用MediaCrawler，使用CLI参数注入配置
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
        self.timeout = 120
        self.retry_times = 3
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
        config_json_path = os.path.join(output_dir, "mc_config.json")
        with open(config_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "PLATFORM": platform,
                "KEYWORDS": keyword,
                "LOGIN_TYPE": "cookie",
                "COOKIES": cookie,
                "CRAWLER_TYPE": "search",
                "CRAWLER_MAX_NOTES_COUNT": max_count,
                "HEADLESS": True,
                "ENABLE_CDP_MODE": False,
                "CDP_CONNECT_EXISTING": False,
                "SAVE_LOGIN_STATE": False,
                "SAVE_DATA_OPTION": "jsonl",
                "SAVE_DATA_PATH": output_dir,
                "ENABLE_GET_COMMENTS": False,
                "ENABLE_GET_SUB_COMMENTS": False,
                "ENABLE_IP_PROXY": False,
                "START_PAGE": 1,
                "MAX_CONCURRENCY_NUM": 1,
            }, f)

        # Run MediaCrawler by patching config before import.
        # We use a subprocess with -c to ensure a clean module state.
        script = (
            "import sys, json, os\n"
            f"sys.path.insert(0, {_escape_py_str(media_crawler_dir)})\n"
            "with open(" + _escape_py_str(config_json_path) + ") as _f:\n"
            "    _overrides = json.load(_f)\n"
            "import config\n"
            "for _k, _v in _overrides.items():\n"
            "    setattr(config, _k, _v)\n"
            "from tools.app_runner import run\n"
            "from main import main, async_cleanup\n"
            "run(main, async_cleanup, cleanup_timeout_seconds=15.0)\n"
        )

        process = await asyncio.create_subprocess_exec(
            sys.executable, "-c", script,
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
                    f"爬虫执行失败（exit={process.returncode}）：{error_msg}\n{stdout_msg}"
                )

            return True

        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"爬虫执行超时（{self.timeout}秒）")

    async def _random_delay(self):
        delay = random.uniform(2, 5)
        await asyncio.sleep(delay)


def _escape_py_str(s: str) -> str:
    return json.dumps(s)


crawler_runner = MediaCrawlerRunner()
