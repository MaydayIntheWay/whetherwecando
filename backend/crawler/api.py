"""
统一爬虫入口 — 封装 mock / 真实爬取切换，主验证流程的唯一调用点
"""
import os
import logging
from typing import List

from models.schemas import CleanedItem
from .models import Platform

logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("USE_MOCK_CRAWLER", "false").lower() in ("true", "1", "yes")


async def crawl_keywords(
    keywords: List[str],
    items_per_keyword: int = 10,
    use_mock: bool = None,
    task_id: str = None,
) -> List[CleanedItem]:
    """
    根据关键词在中文平台上爬取数据。

    Args:
        keywords: 搜索关键词列表
        items_per_keyword: 每个关键词每平台的最大条目数
        use_mock: 强制使用 mock 数据。None 时读取 USE_MOCK_CRAWLER 环境变量
    """
    if use_mock is None:
        use_mock = USE_MOCK

    if use_mock:
        logger.info("Using mock crawler data")
        from .mock_data import generate_mock_data
        return generate_mock_data(keywords, items_per_keyword=items_per_keyword)

    return await _crawl_real(keywords, items_per_keyword, task_id)


async def _crawl_real(
    keywords: List[str],
    items_per_keyword: int,
    task_id: str = None,
) -> List[CleanedItem]:
    """通过 MediaCrawlerAdapter 真实爬取，失败时自动 fallback 到 mock 数据"""
    from datetime import datetime
    from .auth_manager import AuthManager
    from .media_crawler_adapter import MediaCrawlerAdapter
    from database.connection import get_pool, execute_query

    pool = await get_pool()
    auth_manager = AuthManager(pool)
    adapter = MediaCrawlerAdapter(auth_manager)

    all_items: List[CleanedItem] = []
    platforms = (Platform.XIAOHONGSHU, Platform.ZHIHU)

    for keyword in keywords:
        for platform in platforms:
            try:
                msg = f"[CRAWL] 开始抓取 {platform.value} (关键词: {keyword})"
                print(msg, flush=True)
                logger.info(msg)
                raw_items = await adapter.crawl(
                    platform=platform,
                    keyword=keyword,
                    max_count=items_per_keyword,
                )
                platform_items = []
                for item_dict in raw_items:
                    try:
                        item = CleanedItem(**item_dict)
                        platform_items.append(item)
                        all_items.append(item)
                    except Exception:
                        pass

                msg = f"[CRAWL] {platform.value} 完成 (关键词: {keyword}) → {len(platform_items)} 条"
                print(msg, flush=True)
                logger.info(msg)

                # 增量写入数据库，让前端能感知进度
                if task_id and platform_items:
                    now = datetime.now()
                    for item in platform_items:
                        try:
                            await execute_query(
                                """INSERT INTO crawl_results
                                (task_id, platform, keyword, content, source_url, engagement, emotion_intensity, crawled_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                                task_id,
                                item.platform,
                                keyword,
                                item.content[:500],
                                item.source_url,
                                item.engagement,
                                item.emotion_intensity,
                                now,
                            )
                        except Exception:
                            pass
                    print(f"[CRAWL] 已写入 {len(platform_items)} 条 {platform.value} 数据到数据库", flush=True)

            except ValueError as e:
                msg = f"[CRAWL] 跳过 {platform.value} (关键词={keyword}): {e}"
                print(msg, flush=True)
                logger.warning(msg)
            except Exception as e:
                msg = f"[CRAWL] {platform.value} 失败 (关键词={keyword}): {e}"
                print(msg, flush=True)
                logger.error(msg)

    if not all_items:
        logger.warning(
            "真实爬取未返回任何结果，fallback 到 mock 数据"
        )
        from .mock_data import generate_mock_data
        return generate_mock_data(keywords, items_per_keyword=items_per_keyword)

    return all_items
