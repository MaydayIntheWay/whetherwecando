"""
小红书爬虫封装
"""
import asyncio
import random
from typing import List
from models import CleanedItem
from crawler.base import BaseCrawler


class XiaohongshuCrawler(BaseCrawler):
    """小红书爬虫"""
    
    def __init__(self):
        super().__init__(platform="xiaohongshu")
        self.request_delay = random.uniform(2.0, 5.0)
    
    async def crawl_by_keyword(self, keyword: str, max_count: int = 20) -> List[CleanedItem]:
        """
        根据关键词爬取小红书笔记
        
        Args:
            keyword: 搜索关键词
            max_count: 最大爬取数量
            
        Returns:
            清洗后的数据列表
        """
        await asyncio.sleep(self.request_delay)
        
        results: List[CleanedItem] = []
        
        # TODO: 集成MediaCrawler实际爬取逻辑
        # 当前返回空列表，等待MediaCrawler集成
        
        return results
    
    def parse_note(self, note_data: dict) -> CleanedItem:
        """
        解析小红书笔记数据
        
        Args:
            note_data: 原始笔记数据
            
        Returns:
            清洗后的数据项
        """
        return CleanedItem(
            content=note_data.get("content", ""),
            source_url=note_data.get("source_url", ""),
            platform="xiaohongshu",
            engagement=note_data.get("engagement", 0),
            emotion_intensity=self._detect_emotion(note_data.get("content", ""))
        )
    
    def _detect_emotion(self, content: str) -> str:
        """检测情绪强度"""
        strong_keywords = ["太", "真的", "非常", "超级", "特别", "崩溃", "绝望"]
        weak_keywords = ["有点", "稍微", "可能", "也许"]
        
        for kw in strong_keywords:
            if kw in content:
                return "强烈"
        
        for kw in weak_keywords:
            if kw in content:
                return "轻微"
        
        return "一般"
