"""
爬虫模块单元测试
"""
import pytest
from crawler import (
    BaseCrawler,
    XiaohongshuCrawler,
    ZhihuCrawler,
    safe_crawl,
    crawl_keywords_parallel
)
from models import CleanedItem


class TestXiaohongshuCrawler:
    """小红书爬虫测试"""
    
    def test_init(self):
        """测试初始化"""
        crawler = XiaohongshuCrawler()
        assert crawler.platform == "xiaohongshu"
        assert 2.0 <= crawler.request_delay <= 5.0
    
    def test_parse_note(self):
        """测试笔记解析"""
        crawler = XiaohongshuCrawler()
        note_data = {
            "content": "这个产品真的太难用了，崩溃",
            "source_url": "https://www.xiaohongshu.com/test/123",
            "engagement": 1000
        }
        result = crawler.parse_note(note_data)
        
        assert isinstance(result, CleanedItem)
        assert result.platform == "xiaohongshu"
        assert result.source_url == "https://www.xiaohongshu.com/test/123"
        assert result.engagement == 1000
        assert result.emotion_intensity == "强烈"
    
    def test_detect_emotion_strong(self):
        """测试情绪检测 - 强烈"""
        crawler = XiaohongshuCrawler()
        assert crawler._detect_emotion("这个真的太崩溃了") == "强烈"
        assert crawler._detect_emotion("非常绝望") == "强烈"
    
    def test_detect_emotion_weak(self):
        """测试情绪检测 - 轻微"""
        crawler = XiaohongshuCrawler()
        assert crawler._detect_emotion("有点问题") == "轻微"
        assert crawler._detect_emotion("也许可以考虑") == "轻微"
    
    def test_detect_emotion_normal(self):
        """测试情绪检测 - 一般"""
        crawler = XiaohongshuCrawler()
        assert crawler._detect_emotion("这个产品还可以") == "一般"
    
    @pytest.mark.asyncio
    async def test_crawl_by_keyword(self):
        """测试关键词爬取"""
        crawler = XiaohongshuCrawler()
        results = await crawler.crawl_by_keyword("测试关键词", max_count=5)
        assert isinstance(results, list)
        # 当前返回空列表，等待MediaCrawler集成


class TestZhihuCrawler:
    """知乎爬虫测试"""
    
    def test_init(self):
        """测试初始化"""
        crawler = ZhihuCrawler()
        assert crawler.platform == "zhihu"
        assert 2.0 <= crawler.request_delay <= 5.0
    
    def test_parse_question(self):
        """测试问答解析"""
        crawler = ZhihuCrawler()
        question_data = {
            "title": "有什么好用的工具推荐？",
            "excerpt": "真的太难找了，崩溃",
            "source_url": "https://www.zhihu.com/question/123",
            "answer_count": 50
        }
        result = crawler.parse_question(question_data)
        
        assert isinstance(result, CleanedItem)
        assert result.platform == "zhihu"
        assert result.source_url == "https://www.zhihu.com/question/123"
        assert result.engagement == 50
        assert result.emotion_intensity == "强烈"
    
    @pytest.mark.asyncio
    async def test_crawl_by_keyword(self):
        """测试关键词爬取"""
        crawler = ZhihuCrawler()
        results = await crawler.crawl_by_keyword("测试关键词", max_count=5)
        assert isinstance(results, list)


class TestErrorHandler:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_safe_crawl_success(self):
        """测试安全爬取 - 成功"""
        crawler = XiaohongshuCrawler()
        results = await safe_crawl(crawler, "测试", max_count=5, retry_times=1)
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_crawl_keywords_parallel(self):
        """测试并发爬取"""
        crawler = XiaohongshuCrawler()
        keywords = ["关键词1", "关键词2"]
        results = await crawl_keywords_parallel(
            crawler, keywords, 
            max_count_per_keyword=5, 
            concurrency=2
        )
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
