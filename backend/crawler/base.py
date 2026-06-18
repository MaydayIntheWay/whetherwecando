"""
爬虫基类定义
"""
from abc import ABC, abstractmethod
from typing import List
from models import CleanedItem


class BaseCrawler(ABC):
    """爬虫抽象基类"""
    
    def __init__(self, platform: str):
        self.platform = platform
    
    @abstractmethod
    async def crawl_by_keyword(self, keyword: str, max_count: int = 20) -> List[CleanedItem]:
        """
        根据关键词爬取数据
        
        Args:
            keyword: 搜索关键词
            max_count: 最大爬取数量
            
        Returns:
            清洗后的数据列表
        """
        pass
    
    def log_error(self, keyword: str, error: Exception):
        """记录爬取错误"""
        print(f"❌ [{self.platform}] 爬取关键词 '{keyword}' 失败: {type(error).__name__}: {error}")
