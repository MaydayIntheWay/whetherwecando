"""
情绪强度检测器
"""
import re
from typing import Literal

EmotionIntensity = Literal['strong', 'medium', 'weak']

STRONG_EMOTION_WORDS = [
    '太', '真的', '非常', '超级', '极其', '特别', '超级', '绝了',
    '神了', '绝了', '爱死', '太棒了', '太好了', '太赞了', '强烈推荐',
    '必须', '一定要', '千万别错过', '后悔没早', '相见恨晚',
    '救命', '绝绝子', 'yyds', '太香了', '太好用了', '无敌',
    '完美', '惊艳', '震撼', '不可思议', '难以置信'
]

MEDIUM_EMOTION_WORDS = [
    '挺', '比较', '还算', '蛮', '有点儿', '稍微', '略',
    '不错', '还可以', '还行', '挺好', '蛮好', '值得',
    '推荐', '喜欢', '满意', '实用', '方便'
]

WEAK_EMOTION_WORDS = [
    '可能', '也许', '大概', '或许', '好像', '似乎',
    '一般', '普通', '正常', '常见', '基础'
]


class EmotionDetector:
    def __init__(self):
        self.strong_pattern = self._build_pattern(STRONG_EMOTION_WORDS)
        self.medium_pattern = self._build_pattern(MEDIUM_EMOTION_WORDS)
        self.weak_pattern = self._build_pattern(WEAK_EMOTION_WORDS)
    
    def _build_pattern(self, words: list) -> re.Pattern:
        pattern = '|'.join(re.escape(word) for word in words)
        return re.compile(pattern)
    
    def detect(self, text: str) -> EmotionIntensity:
        if not text:
            return 'weak'
        
        strong_matches = len(self.strong_pattern.findall(text))
        medium_matches = len(self.medium_pattern.findall(text))
        weak_matches = len(self.weak_pattern.findall(text))
        
        if strong_matches >= 2 or (strong_matches >= 1 and medium_matches >= 1):
            return 'strong'
        elif strong_matches >= 1 or medium_matches >= 2:
            return 'medium'
        else:
            return 'weak'
    
    def get_score(self, text: str) -> float:
        intensity = self.detect(text)
        scores = {'strong': 1.0, 'medium': 0.6, 'weak': 0.3}
        return scores[intensity]


emotion_detector = EmotionDetector()
