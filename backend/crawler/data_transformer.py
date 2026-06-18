"""
数据转换器
"""
import re
from typing import Optional
from models.schemas import CleanedItem
from .utils.emotion_detector import emotion_detector


class DataTransformer:
    PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')
    EMAIL_PATTERN = re.compile(r'[\w.-]+@[\w.-]+\.\w+')
    ID_CARD_PATTERN = re.compile(r'\d{17}[\dXx]')
    
    def transform_xiaohongshu_note(self, note_data: dict) -> Optional[CleanedItem]:
        note_id = note_data.get('note_id')
        if not note_id:
            return None
        
        content = note_data.get('note_desc', '')
        content = self._filter_sensitive_info(content)
        content = content[:1000]
        
        source_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        
        like_count = note_data.get('like_count', 0) or 0
        comment_count = note_data.get('comment_count', 0) or 0
        collect_count = note_data.get('collect_count', 0) or 0
        engagement = like_count + comment_count + collect_count
        
        emotion_intensity = emotion_detector.detect(content)
        
        return CleanedItem(
            content=content,
            source_url=source_url,
            platform='xiaohongshu',
            engagement=engagement,
            emotion_intensity=emotion_intensity
        )
    
    def transform_zhihu_question(self, question_data: dict) -> Optional[CleanedItem]:
        question_id = question_data.get('id')
        if not question_id:
            return None
        
        title = question_data.get('title', '')
        excerpt = question_data.get('excerpt', '')
        content = f"{title}\n{excerpt}".strip()
        content = self._filter_sensitive_info(content)
        content = content[:500]
        
        source_url = f"https://www.zhihu.com/question/{question_id}"
        
        answer_count = question_data.get('answer_count', 0) or 0
        engagement = answer_count
        
        emotion_intensity = emotion_detector.detect(content)
        
        return CleanedItem(
            content=content,
            source_url=source_url,
            platform='zhihu',
            engagement=engagement,
            emotion_intensity=emotion_intensity
        )
    
    def _filter_sensitive_info(self, text: str) -> str:
        text = self.PHONE_PATTERN.sub('****', text)
        text = self.EMAIL_PATTERN.sub('****', text)
        text = self.ID_CARD_PATTERN.sub('****', text)
        return text
    
    def transform_batch(
        self, 
        raw_data_list: list[dict], 
        platform: str
    ) -> list[CleanedItem]:
        results = []
        
        for raw_data in raw_data_list:
            if platform == 'xiaohongshu':
                item = self.transform_xiaohongshu_note(raw_data)
            elif platform == 'zhihu':
                item = self.transform_zhihu_question(raw_data)
            else:
                continue
            
            if item and item.source_url:
                results.append(item)
        
        return results


data_transformer = DataTransformer()
