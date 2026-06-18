"""
MediaCrawler输出捕获器
"""
import asyncio
import json
from pathlib import Path
from typing import List


class MediaCrawlerOutputCapture:
    def __init__(self):
        self.wait_timeout = 30
    
    async def capture_output(
        self,
        output_dir: str,
        platform: str
    ) -> List[dict]:
        output_filename = self._get_output_filename(platform)
        output_path = Path(output_dir) / output_filename
        
        await self._wait_for_output(output_path)
        
        if not output_path.exists():
            raise FileNotFoundError(f"输出文件不存在：{output_path}")
        
        results = []
        with open(output_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        results.append(data)
                    except json.JSONDecodeError:
                        continue
        
        return self._deduplicate(results)
    
    async def _wait_for_output(self, output_path: Path):
        for _ in range(self.wait_timeout):
            if output_path.exists():
                return
            await asyncio.sleep(1)
    
    def _get_output_filename(self, platform: str) -> str:
        platform_map = {
            'xiaohongshu': 'xhs_search.jsonl',
            'xhs': 'xhs_search.jsonl',
            'zhihu': 'zhihu_search.jsonl'
        }
        
        platform_lower = platform.lower()
        if platform_lower not in platform_map:
            raise ValueError(f"不支持的平台：{platform}")
        
        return platform_map[platform_lower]
    
    def _deduplicate(self, results: List[dict]) -> List[dict]:
        seen = set()
        unique_results = []
        
        for item in results:
            source_url = item.get('source_url') or item.get('note_id') or item.get('id')
            if source_url and source_url not in seen:
                seen.add(source_url)
                unique_results.append(item)
        
        return unique_results


output_capture = MediaCrawlerOutputCapture()
