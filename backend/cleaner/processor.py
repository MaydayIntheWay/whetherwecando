"""
数据清洗处理器
"""
import re
from typing import List, Set
from models import CleanedItem


class DataCleaner:
    """数据清洗处理器"""
    
    def __init__(self):
        self.ad_patterns = [
            r"广告",
            r"推广",
            r"赞助",
            r"合作",
            r"福利",
            r"抽奖",
            r"优惠",
            r"领取",
            r"点击链接",
            r"私信我",
        ]
        self._compiled_patterns = [re.compile(p) for p in self.ad_patterns]
    
    def deduplicate(self, items: List[CleanedItem]) -> List[CleanedItem]:
        """
        基于source_url去重
        
        Args:
            items: 数据列表
            
        Returns:
            去重后的数据列表
        """
        seen_urls: Set[str] = set()
        unique_items: List[CleanedItem] = []
        
        for item in items:
            if item.source_url not in seen_urls:
                seen_urls.add(item.source_url)
                unique_items.append(item)
        
        return unique_items
    
    def is_ad_content(self, content: str) -> bool:
        """
        判断是否为广告内容
        
        Args:
            content: 内容文本
            
        Returns:
            是否为广告
        """
        for pattern in self._compiled_patterns:
            if pattern.search(content):
                return True
        return False
    
    def filter_ads(self, items: List[CleanedItem]) -> List[CleanedItem]:
        """
        过滤广告内容
        
        Args:
            items: 数据列表
            
        Returns:
            过滤后的数据列表
        """
        return [item for item in items if not self.is_ad_content(item.content)]
    
    def extract_valid_fields(self, item: CleanedItem) -> CleanedItem:
        """
        提取有效字段，清理无效内容
        
        Args:
            item: 数据项
            
        Returns:
            清理后的数据项
        """
        content = item.content.strip()
        content = re.sub(r'\s+', ' ', content)
        
        return CleanedItem(
            content=content,
            source_url=item.source_url,
            platform=item.platform,
            engagement=max(0, item.engagement),
            emotion_intensity=item.emotion_intensity
        )
    
    def clean(self, items: List[CleanedItem]) -> List[CleanedItem]:
        """
        数据清洗主函数
        
        Args:
            items: 原始数据列表
            
        Returns:
            清洗后的数据列表
        """
        if not items:
            return []
        
        cleaned = self.deduplicate(items)
        cleaned = self.filter_ads(cleaned)
        cleaned = [self.extract_valid_fields(item) for item in cleaned]
        
        return cleaned
