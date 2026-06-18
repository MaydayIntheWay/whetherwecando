"""
数据清洗模块单元测试
"""
import pytest
from cleaner import DataCleaner
from models import CleanedItem


class TestDataCleaner:
    """数据清洗测试"""
    
    def test_deduplicate(self):
        """测试去重"""
        cleaner = DataCleaner()
        items = [
            CleanedItem(content="内容1", source_url="url1", platform="xhs", engagement=10),
            CleanedItem(content="内容2", source_url="url1", platform="xhs", engagement=20),
            CleanedItem(content="内容3", source_url="url2", platform="xhs", engagement=30),
        ]
        result = cleaner.deduplicate(items)
        
        assert len(result) == 2
        assert result[0].source_url == "url1"
        assert result[1].source_url == "url2"
    
    def test_is_ad_content_true(self):
        """测试广告检测 - 是广告"""
        cleaner = DataCleaner()
        
        assert cleaner.is_ad_content("这是一个广告内容") is True
        assert cleaner.is_ad_content("推广产品") is True
        assert cleaner.is_ad_content("点击链接领取福利") is True
        assert cleaner.is_ad_content("私信我获取优惠") is True
    
    def test_is_ad_content_false(self):
        """测试广告检测 - 不是广告"""
        cleaner = DataCleaner()
        
        assert cleaner.is_ad_content("这个产品真的太难用了") is False
        assert cleaner.is_ad_content("有没有好用的工具推荐") is False
        assert cleaner.is_ad_content("崩溃了，找不到解决方案") is False
    
    def test_filter_ads(self):
        """测试过滤广告"""
        cleaner = DataCleaner()
        items = [
            CleanedItem(content="正常内容1", source_url="url1", platform="xhs"),
            CleanedItem(content="这是一个广告", source_url="url2", platform="xhs"),
            CleanedItem(content="正常内容2", source_url="url3", platform="xhs"),
            CleanedItem(content="推广产品", source_url="url4", platform="xhs"),
        ]
        result = cleaner.filter_ads(items)
        
        assert len(result) == 2
        assert result[0].content == "正常内容1"
        assert result[1].content == "正常内容2"
    
    def test_extract_valid_fields(self):
        """测试字段提取"""
        cleaner = DataCleaner()
        item = CleanedItem(
            content="  多余空格  的  内容  ",
            source_url="url1",
            platform="xhs",
            engagement=-5,
            emotion_intensity="强烈"
        )
        result = cleaner.extract_valid_fields(item)
        
        assert result.content == "多余空格 的 内容"
        assert result.engagement == 0
        assert result.emotion_intensity == "强烈"
    
    def test_clean_full_pipeline(self):
        """测试完整清洗流程"""
        cleaner = DataCleaner()
        items = [
            CleanedItem(content="正常内容1", source_url="url1", platform="xhs", engagement=10),
            CleanedItem(content="正常内容1", source_url="url1", platform="xhs", engagement=20),
            CleanedItem(content="广告内容", source_url="url2", platform="xhs"),
            CleanedItem(content="  正常内容2  ", source_url="url3", platform="xhs"),
        ]
        result = cleaner.clean(items)
        
        assert len(result) == 2
        assert result[0].content == "正常内容1"
        assert result[1].content == "正常内容2"
    
    def test_clean_empty_list(self):
        """测试空列表"""
        cleaner = DataCleaner()
        result = cleaner.clean([])
        
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
