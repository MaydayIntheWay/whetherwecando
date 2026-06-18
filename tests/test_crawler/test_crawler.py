"""
爬虫模块单元测试
"""
import pytest
from crawler.utils.crypto import AESCipher
from crawler.utils.emotion_detector import EmotionDetector
from crawler.data_transformer import DataTransformer


class TestAESCipher:
    def test_encrypt_decrypt(self):
        cipher = AESCipher("ThisIsA32ByteEncryptionKey123456")
        plaintext = "test_cookie_value_123"
        encrypted = cipher.encrypt(plaintext)
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_different_nonce(self):
        cipher = AESCipher("ThisIsA32ByteEncryptionKey123456")
        plaintext = "test_cookie_value"
        encrypted1 = cipher.encrypt(plaintext)
        encrypted2 = cipher.encrypt(plaintext)
        assert encrypted1 != encrypted2
    
    def test_decrypt_invalid_data(self):
        cipher = AESCipher("ThisIsA32ByteEncryptionKey123456")
        with pytest.raises(ValueError):
            cipher.decrypt("invalid_base64_data")


class TestEmotionDetector:
    def test_strong_emotion(self):
        detector = EmotionDetector()
        text = "这个产品真的太棒了！超级好用！"
        assert detector.detect(text) == 'strong'
    
    def test_medium_emotion(self):
        detector = EmotionDetector()
        text = "这个产品还不错，挺实用的"
        assert detector.detect(text) == 'medium'
    
    def test_weak_emotion(self):
        detector = EmotionDetector()
        text = "这是一个普通的产品"
        assert detector.detect(text) == 'weak'
    
    def test_empty_text(self):
        detector = EmotionDetector()
        assert detector.detect("") == 'weak'


class TestDataTransformer:
    def test_transform_xiaohongshu_note(self):
        transformer = DataTransformer()
        note_data = {
            'note_id': 'test123',
            'note_desc': '这是一个测试笔记，太棒了',
            'like_count': 100,
            'comment_count': 20,
            'collect_count': 30
        }
        result = transformer.transform_xiaohongshu_note(note_data)
        assert result is not None
        assert result.platform == 'xiaohongshu'
        assert result.source_url == 'https://www.xiaohongshu.com/explore/test123'
        assert result.engagement == 150
    
    def test_transform_zhihu_question(self):
        transformer = DataTransformer()
        question_data = {
            'id': '456789',
            'title': '测试问题',
            'excerpt': '这是问题描述',
            'answer_count': 50
        }
        result = transformer.transform_zhihu_question(question_data)
        assert result is not None
        assert result.platform == 'zhihu'
        assert result.source_url == 'https://www.zhihu.com/question/456789'
        assert result.engagement == 50
    
    def test_filter_sensitive_info(self):
        transformer = DataTransformer()
        text = "联系我：13812345678，邮箱test@example.com"
        filtered = transformer._filter_sensitive_info(text)
        assert '13812345678' not in filtered
        assert 'test@example.com' not in filtered
        assert '****' in filtered
    
    def test_transform_batch(self):
        transformer = DataTransformer()
        raw_data_list = [
            {'note_id': '1', 'note_desc': '测试1', 'like_count': 10},
            {'note_id': '2', 'note_desc': '测试2', 'like_count': 20},
        ]
        results = transformer.transform_batch(raw_data_list, 'xiaohongshu')
        assert len(results) == 2
        assert all(item.source_url for item in results)
