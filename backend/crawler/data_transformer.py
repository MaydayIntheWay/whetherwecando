"""
数据转换器 — 将 MediaCrawler 原始输出转换为 CleanedItem
"""
import re
from typing import Optional
from models.schemas import CleanedItem
from .utils.emotion_detector import emotion_detector


def _parse_count(value) -> int:
    """解析中文数字格式: 纯数字、'1.5万'、'10万+' 等"""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip().rstrip('+').replace(',', '').replace('，', '')
    if not s:
        return 0
    if '万' in s:
        try:
            return int(float(s.replace('万', '')) * 10000)
        except ValueError:
            pass
    try:
        return int(float(s))
    except ValueError:
        return 0


class DataTransformer:
    PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')
    EMAIL_PATTERN = re.compile(r'[\w.-]+@[\w.-]+\.\w+')
    ID_CARD_PATTERN = re.compile(r'\d{17}[\dXx]')

    def transform_xiaohongshu_note(self, note_data: dict) -> Optional[CleanedItem]:
        note_id = note_data.get('note_id')
        if not note_id:
            return None

        title = note_data.get('title', '') or ''
        desc = note_data.get('desc', '') or ''
        content = f"{title}\n{desc}".strip()
        content = self._filter_sensitive_info(content)
        content = content[:1000]

        source_url = note_data.get('note_url', '') or f"https://www.xiaohongshu.com/explore/{note_id}"

        like_count = _parse_count(note_data.get('liked_count'))
        comment_count = _parse_count(note_data.get('comment_count'))
        collect_count = _parse_count(note_data.get('collected_count'))
        share_count = _parse_count(note_data.get('share_count'))
        engagement = like_count + comment_count + collect_count + share_count

        return CleanedItem(
            content=content,
            source_url=source_url,
            platform='xiaohongshu',
            engagement=engagement,
            emotion_intensity=emotion_detector.detect(content),
        )

    def transform_zhihu_question(self, question_data: dict) -> Optional[CleanedItem]:
        content_id = question_data.get('content_id') or question_data.get('id') or question_data.get('question_id')
        if not content_id:
            return None

        title = question_data.get('title', '') or ''
        body = question_data.get('content_text', '') or question_data.get('desc', '') or ''
        content = f"{title}\n{body}".strip()
        content = self._filter_sensitive_info(content)
        content = content[:500]

        source_url = question_data.get('content_url', '') or ''
        if not source_url and str(content_id).isdigit():
            source_url = f"https://www.zhihu.com/question/{content_id}"

        voteup_count = _parse_count(question_data.get('voteup_count'))
        comment_count = _parse_count(question_data.get('comment_count'))
        engagement = voteup_count + comment_count

        return CleanedItem(
            content=content,
            source_url=source_url,
            platform='zhihu',
            engagement=engagement,
            emotion_intensity=emotion_detector.detect(content),
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
