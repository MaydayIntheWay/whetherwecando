"""
MediaCrawler适配器 — 集成MediaCrawler框架

提供两种爬取模式：
- crawl(): 批处理模式，等待子进程完成后一次性返回所有结果
- crawl_stream(): 流式模式，子进程边写 JSONL 边 yield 结果，实现实时进度
"""
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable, List, AsyncIterator
from .auth_manager import AuthManager
from .data_transformer import DataTransformer
from .media_crawler_runner import MediaCrawlerRunner
from .media_crawler_output import MediaCrawlerOutputCapture
from .models import Platform


class MediaCrawlerAdapter:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.runner = MediaCrawlerRunner()
        self.output_capture = MediaCrawlerOutputCapture()
        self.transformer = DataTransformer()
        self.media_crawler_dir = str(Path(__file__).parent / "MediaCrawler")

    async def crawl_xiaohongshu(
        self,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> List[dict]:
        return await self._crawl_platform(
            platform_code="xhs",
            platform_name="xiaohongshu",
            keyword=keyword,
            max_count=max_count,
            progress_callback=progress_callback,
        )

    async def crawl_zhihu(
        self,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> List[dict]:
        return await self._crawl_platform(
            platform_code="zhihu",
            platform_name="zhihu",
            keyword=keyword,
            max_count=max_count,
            progress_callback=progress_callback,
        )

    async def _crawl_platform(
        self,
        platform_code: str,
        platform_name: str,
        keyword: str,
        max_count: int,
        progress_callback: Optional[Callable],
    ) -> List[dict]:
        cookie = await self.auth_manager.get_decrypted_cookie(
            Platform.XIAOHONGSHU if platform_code == "xhs" else Platform.ZHIHU
        )
        if not cookie:
            raise ValueError(f"{platform_name}登录态未配置或已失效")

        temp_dir = tempfile.mkdtemp(prefix=f"media_crawler_{platform_code}_")
        print(f"[ADAPTER] 开始爬取 {platform_name} (关键词: {keyword})", flush=True)

        try:
            await self.runner.run_crawler(
                media_crawler_dir=self.media_crawler_dir,
                platform=platform_code,
                keyword=keyword,
                cookie=cookie,
                max_count=max_count,
                output_dir=temp_dir,
                progress_callback=progress_callback,
            )

            raw_data_list = await self.output_capture.capture_output(
                output_dir=temp_dir,
                platform=platform_code,
            )
            print(f"[ADAPTER] {platform_name} 原始数据: {len(raw_data_list)} 条", flush=True)

            cleaned_items = []
            for i, raw_data in enumerate(raw_data_list):
                if platform_code == "xhs":
                    item = self.transformer.transform_xiaohongshu_note(raw_data)
                else:
                    item = self.transformer.transform_zhihu_question(raw_data)
                if item and item.source_url:
                    cleaned_items.append(item.model_dump())

            print(f"[ADAPTER] {platform_name} 有效数据: {len(cleaned_items)} 条 (关键词: {keyword})", flush=True)
            return cleaned_items

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def crawl_stream(
        self,
        platform_code: str,
        platform_name: str,
        keyword: str,
        max_count: int = 50,
    ) -> AsyncIterator[dict]:
        """
        流式爬取 — 子进程边写 JSONL 边 yield 结果，实现逐条实时进度。

        与 crawl() 不同，此方法不等待子进程结束，而是在子进程运行期间
        实时 tail JSONL 输出文件，每写入一条新数据就立即 yield。
        """
        cookie = await self.auth_manager.get_decrypted_cookie(
            Platform.XIAOHONGSHU if platform_code == "xhs" else Platform.ZHIHU
        )
        if not cookie:
            if platform_code == "zhihu":
                hint = (
                    "知乎登录态未配置或已失效。"
                    "知乎 Cookie 必须包含 d_c0（API签名）和 z_c0（登录验证），"
                    "请从浏览器 zhihu.com 域名下复制完整 Cookie"
                )
                raise ValueError(hint)
            raise ValueError(f"{platform_name}登录态未配置或已失效")

        temp_dir = tempfile.mkdtemp(prefix=f"media_crawler_{platform_code}_")
        subprocess_done = asyncio.Event()

        async def _run_subprocess():
            try:
                await self.runner.run_crawler(
                    media_crawler_dir=self.media_crawler_dir,
                    platform=platform_code,
                    keyword=keyword,
                    cookie=cookie,
                    max_count=max_count,
                    output_dir=temp_dir,
                )
            finally:
                subprocess_done.set()

        subprocess_task = asyncio.create_task(_run_subprocess())

        try:
            raw_count = 0
            yield_count = 0
            async for raw_data in self.output_capture.stream_output(
                temp_dir, platform_code, subprocess_done,
            ):
                raw_count += 1
                if platform_code == "xhs":
                    item = self.transformer.transform_xiaohongshu_note(raw_data)
                else:
                    item = self.transformer.transform_zhihu_question(raw_data)
                if item and item.source_url:
                    yield_count += 1
                    yield item.model_dump()
                else:
                    content_id = raw_data.get("content_id") or raw_data.get("question_id") or raw_data.get("id") or "?"
                    print(f"[ADAPTER] 转换失败 #{raw_count}: cid={str(content_id)[:50]}, has_item={item is not None}, has_url={bool(item and item.source_url)}", flush=True)

            print(f"[ADAPTER] {platform_name} 流式读取完成: raw={raw_count}, yield={yield_count}", flush=True)
            await subprocess_task

        except Exception:
            subprocess_done.set()
            if not subprocess_task.done():
                subprocess_task.cancel()
            raise
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def crawl(
        self,
        platform: Platform,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> List[dict]:
        if platform == Platform.XIAOHONGSHU:
            return await self.crawl_xiaohongshu(keyword, max_count, progress_callback)
        elif platform == Platform.ZHIHU:
            return await self.crawl_zhihu(keyword, max_count, progress_callback)
        else:
            raise ValueError(f"不支持的平台：{platform}")
