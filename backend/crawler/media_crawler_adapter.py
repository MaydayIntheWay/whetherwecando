"""
MediaCrawler适配器（重构版）- 真实集成MediaCrawler框架
"""
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable, List
from .auth_manager import AuthManager
from .data_transformer import DataTransformer
from .media_crawler_config import MediaCrawlerConfigGenerator
from .media_crawler_runner import MediaCrawlerRunner
from .media_crawler_output import MediaCrawlerOutputCapture
from .models import Platform


class MediaCrawlerAdapter:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.config_generator = MediaCrawlerConfigGenerator()
        self.runner = MediaCrawlerRunner()
        self.output_capture = MediaCrawlerOutputCapture()
        self.transformer = DataTransformer()
        
        self.media_crawler_dir = Path(__file__).parent / "MediaCrawler"
    
    async def crawl_xiaohongshu(
        self,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> List[dict]:
        cookie = await self.auth_manager.get_decrypted_cookie(Platform.XIAOHONGSHU)
        if not cookie:
            raise ValueError("小红书登录态未配置或已失效")
        
        temp_dir = tempfile.mkdtemp(prefix="media_crawler_xhs_")
        
        try:
            if progress_callback:
                await progress_callback(
                    current=0,
                    total=max_count,
                    message="正在生成配置文件..."
                )
            
            config_path = self.config_generator.generate_config(
                platform="xiaohongshu",
                keyword=keyword,
                cookie=cookie,
                max_count=max_count,
                output_dir=temp_dir
            )
            
            if progress_callback:
                await progress_callback(
                    current=0,
                    total=max_count,
                    message="正在启动浏览器..."
                )
            
            await self.runner.run_crawler(
                config_path=config_path,
                media_crawler_dir=str(self.media_crawler_dir),
                progress_callback=progress_callback
            )
            
            if progress_callback:
                await progress_callback(
                    current=0,
                    total=max_count,
                    message="正在读取爬取结果..."
                )
            
            raw_data_list = await self.output_capture.capture_output(
                output_dir=temp_dir,
                platform="xiaohongshu"
            )
            
            cleaned_items = []
            for i, raw_data in enumerate(raw_data_list):
                item = self.transformer.transform_xiaohongshu_note(raw_data)
                if item and item.source_url:
                    cleaned_items.append(item.model_dump())
                
                if progress_callback:
                    await progress_callback(
                        current=i + 1,
                        total=len(raw_data_list),
                        message=f"已处理 {i + 1}/{len(raw_data_list)} 条"
                    )
            
            return cleaned_items
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def crawl_zhihu(
        self,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> List[dict]:
        cookie = await self.auth_manager.get_decrypted_cookie(Platform.ZHIHU)
        if not cookie:
            raise ValueError("知乎登录态未配置或已失效")
        
        temp_dir = tempfile.mkdtemp(prefix="media_crawler_zhihu_")
        
        try:
            if progress_callback:
                await progress_callback(
                    current=0,
                    total=max_count,
                    message="正在生成配置文件..."
                )
            
            config_path = self.config_generator.generate_config(
                platform="zhihu",
                keyword=keyword,
                cookie=cookie,
                max_count=max_count,
                output_dir=temp_dir
            )
            
            if progress_callback:
                await progress_callback(
                    current=0,
                    total=max_count,
                    message="正在启动浏览器..."
                )
            
            await self.runner.run_crawler(
                config_path=config_path,
                media_crawler_dir=str(self.media_crawler_dir),
                progress_callback=progress_callback
            )
            
            if progress_callback:
                await progress_callback(
                    current=0,
                    total=max_count,
                    message="正在读取爬取结果..."
                )
            
            raw_data_list = await self.output_capture.capture_output(
                output_dir=temp_dir,
                platform="zhihu"
            )
            
            cleaned_items = []
            for i, raw_data in enumerate(raw_data_list):
                item = self.transformer.transform_zhihu_question(raw_data)
                if item and item.source_url:
                    cleaned_items.append(item.model_dump())
                
                if progress_callback:
                    await progress_callback(
                        current=i + 1,
                        total=len(raw_data_list),
                        message=f"已处理 {i + 1}/{len(raw_data_list)} 条"
                    )
            
            return cleaned_items
            
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
