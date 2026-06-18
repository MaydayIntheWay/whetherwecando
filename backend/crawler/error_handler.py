"""
爬虫错误处理
"""
import asyncio
from typing import List, Callable, Optional
from models import CleanedItem
from crawler.base import BaseCrawler


class CrawlerError(Exception):
    """爬虫错误基类"""
    pass


class PlatformBlockedError(CrawlerError):
    """平台封禁错误"""
    pass


class LoginRequiredError(CrawlerError):
    """需要登录错误"""
    pass


async def safe_crawl(
    crawler: BaseCrawler,
    keyword: str,
    max_count: int = 20,
    retry_times: int = 3,
    retry_delay: float = 2.0
) -> List[CleanedItem]:
    """
    安全爬取，带错误处理和重试
    
    Args:
        crawler: 爬虫实例
        keyword: 关键词
        max_count: 最大数量
        retry_times: 重试次数
        retry_delay: 重试延迟（秒）
        
    Returns:
        清洗后的数据列表，失败返回空列表
    """
    last_error: Optional[Exception] = None
    
    for attempt in range(retry_times):
        try:
            results = await crawler.crawl_by_keyword(keyword, max_count)
            return results
        except PlatformBlockedError as e:
            crawler.log_error(keyword, e)
            return []
        except LoginRequiredError as e:
            crawler.log_error(keyword, e)
            return []
        except Exception as e:
            last_error = e
            crawler.log_error(keyword, e)
            if attempt < retry_times - 1:
                await asyncio.sleep(retry_delay)
    
    return []


async def crawl_keywords_parallel(
    crawler: BaseCrawler,
    keywords: List[str],
    max_count_per_keyword: int = 20,
    concurrency: int = 3
) -> List[CleanedItem]:
    """
    并发爬取多个关键词
    
    Args:
        crawler: 爬虫实例
        keywords: 关键词列表
        max_count_per_keyword: 每个关键词最大数量
        concurrency: 并发数
        
    Returns:
        所有关键词的爬取结果
    """
    semaphore = asyncio.Semaphore(concurrency)
    
    async def crawl_with_semaphore(keyword: str) -> List[CleanedItem]:
        async with semaphore:
            return await safe_crawl(crawler, keyword, max_count_per_keyword)
    
    tasks = [crawl_with_semaphore(kw) for kw in keywords]
    results = await asyncio.gather(*tasks)
    
    all_items: List[CleanedItem] = []
    for items in results:
        all_items.extend(items)
    
    return all_items
