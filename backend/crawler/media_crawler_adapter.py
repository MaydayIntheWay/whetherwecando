"""
MediaCrawler适配器
"""
import asyncio
from typing import Optional, Callable
from .auth_manager import AuthManager
from .utils.rate_limiter import rate_limiter
from .models import Platform


class MediaCrawlerAdapter:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self._initialized = False
    
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            pass
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"MediaCrawler初始化失败: {str(e)}")
    
    async def crawl_xiaohongshu(
        self,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> list[dict]:
        await self.initialize()
        
        cookie = await self.auth_manager.get_decrypted_cookie(Platform.XIAOHONGSHU)
        if not cookie:
            raise ValueError("小红书登录态未配置或已失效")
        
        results = []
        
        try:
            for i in range(min(max_count, 10)):
                await rate_limiter.wait()
                
                mock_note = {
                    'note_id': f'mock_note_{i}',
                    'note_desc': f'这是关于"{keyword}"的第{i+1}条小红书笔记内容',
                    'like_count': 100 + i * 10,
                    'comment_count': 20 + i,
                    'collect_count': 50 + i * 5
                }
                results.append(mock_note)
                
                if progress_callback:
                    await progress_callback(
                        current=len(results),
                        total=max_count,
                        message=f"已爬取 {len(results)}/{max_count} 条"
                    )
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"小红书爬取失败: {str(e)}")
    
    async def crawl_zhihu(
        self,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> list[dict]:
        await self.initialize()
        
        cookie = await self.auth_manager.get_decrypted_cookie(Platform.ZHIHU)
        if not cookie:
            raise ValueError("知乎登录态未配置或已失效")
        
        results = []
        
        try:
            for i in range(min(max_count, 10)):
                await rate_limiter.wait()
                
                mock_question = {
                    'id': f'mock_question_{i}',
                    'title': f'关于{keyword}的问题{i+1}',
                    'excerpt': f'这是关于{keyword}的问题描述，包含用户讨论内容...',
                    'answer_count': 30 + i * 5
                }
                results.append(mock_question)
                
                if progress_callback:
                    await progress_callback(
                        current=len(results),
                        total=max_count,
                        message=f"已爬取 {len(results)}/{max_count} 条"
                    )
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"知乎爬取失败: {str(e)}")
    
    async def crawl(
        self,
        platform: Platform,
        keyword: str,
        max_count: int = 50,
        progress_callback: Optional[Callable] = None
    ) -> list[dict]:
        if platform == Platform.XIAOHONGSHU:
            return await self.crawl_xiaohongshu(keyword, max_count, progress_callback)
        elif platform == Platform.ZHIHU:
            return await self.crawl_zhihu(keyword, max_count, progress_callback)
        else:
            raise ValueError(f"不支持的平台: {platform}")
