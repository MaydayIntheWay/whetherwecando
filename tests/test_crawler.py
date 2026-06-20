"""
爬虫模块单元测试 — 统一入口 + DataTransformer + EmotionDetector
"""
import pytest
from crawler import crawl_keywords
from crawler.data_transformer import DataTransformer
from crawler.utils.emotion_detector import EmotionDetector
from models import CleanedItem


class TestUnifiedCrawler:
    """统一爬虫入口测试"""

    @pytest.mark.asyncio
    async def test_crawl_with_mock(self):
        """Mock 模式下返回正确结构的 CleanedItem 列表"""
        results = await crawl_keywords(
            ["AI写作", "知识管理"],
            items_per_keyword=3,
            use_mock=True,
        )
        assert isinstance(results, list)
        assert len(results) > 0
        for item in results:
            assert isinstance(item, CleanedItem)
            assert item.content
            assert item.source_url
            assert item.platform in ("xiaohongshu", "zhihu")

    @pytest.mark.asyncio
    async def test_crawl_single_keyword(self):
        """单个关键词产生结果"""
        results = await crawl_keywords(["测试"], items_per_keyword=5, use_mock=True)
        assert len(results) >= 5

    @pytest.mark.asyncio
    async def test_crawl_empty_keywords(self):
        """空关键词列表返回空列表"""
        results = await crawl_keywords([], items_per_keyword=5, use_mock=True)
        assert isinstance(results, list)
        assert len(results) == 0


class TestDataTransformer:
    """数据转换器测试"""

    def setup_method(self):
        self.transformer = DataTransformer()

    def test_transform_xiaohongshu_note(self):
        note_data = {
            "note_id": "abc123",
            "title": "这个产品评价",
            "desc": "真的太好用了，强烈推荐！",
            "liked_count": "4.8万",
            "comment_count": "1076",
            "collected_count": "2339",
            "share_count": "1956",
        }
        result = self.transformer.transform_xiaohongshu_note(note_data)
        assert result is not None
        assert result.platform == "xiaohongshu"
        assert "explore/abc123" in result.source_url
        # 48000 + 1076 + 2339 + 1956 = 53371
        assert result.engagement == 53371

    def test_transform_xiaohongshu_note_no_id(self):
        """note_id 缺失时返回 None"""
        result = self.transformer.transform_xiaohongshu_note({})
        assert result is None

    def test_transform_zhihu_question(self):
        question_data = {
            "content_id": "649928825",
            "title": "如何评价XX产品？",
            "content_text": "个人认为这个产品很有前景",
            "content_url": "https://www.zhihu.com/question/649928825/answer/3542504754",
            "voteup_count": 1648,
            "comment_count": 63,
        }
        result = self.transformer.transform_zhihu_question(question_data)
        assert result is not None
        assert result.platform == "zhihu"
        assert result.source_url == "https://www.zhihu.com/question/649928825/answer/3542504754"
        assert result.engagement == 1711

    def test_transform_zhihu_question_no_id(self):
        """id 缺失时返回 None"""
        result = self.transformer.transform_zhihu_question({})
        assert result is None

    def test_filter_sensitive_info(self):
        text = "联系我：13812345678，邮箱test@example.com"
        filtered = self.transformer._filter_sensitive_info(text)
        assert "13812345678" not in filtered
        assert "test@example.com" not in filtered
        assert "****" in filtered

    def test_transform_batch(self):
        raw_data_list = [
            {"note_id": "1", "note_desc": "测试1", "like_count": 10},
            {"note_id": "2", "note_desc": "测试2", "like_count": 20},
        ]
        results = self.transformer.transform_batch(raw_data_list, "xiaohongshu")
        assert len(results) == 2
        assert all(item.source_url for item in results)

    def test_transform_batch_skips_invalid(self):
        """batch 转换跳过无效条目"""
        raw_data_list = [
            {"note_id": "1", "note_desc": "有效", "like_count": 10},
            {},  # 无 note_id
            {"note_id": "3", "note_desc": "有效2", "like_count": 5},
        ]
        results = self.transformer.transform_batch(raw_data_list, "xiaohongshu")
        assert len(results) == 2


class TestEmotionDetector:
    """情绪检测器测试"""

    def setup_method(self):
        self.detector = EmotionDetector()

    def test_strong_emotion(self):
        assert self.detector.detect("这个真的太超级好用了！强烈推荐！") == "strong"

    def test_medium_emotion(self):
        assert self.detector.detect("挺不错的，还算满意") == "medium"

    def test_weak_emotion(self):
        assert self.detector.detect("可能一般吧") == "weak"
        assert self.detector.detect("这是一个普通描述") == "weak"

    def test_empty_text(self):
        assert self.detector.detect("") == "weak"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
