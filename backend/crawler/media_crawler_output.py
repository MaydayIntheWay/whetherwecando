"""
MediaCrawler输出捕获器
从MediaCrawler生成的jsonl文件中读取爬取结果。
MediaCrawler输出路径: {save_path}/{platform}/jsonl/search_contents_{date}.jsonl
"""
import asyncio
import glob
import json
from pathlib import Path
from typing import List, Optional


class MediaCrawlerOutputCapture:
    def __init__(self):
        self.wait_timeout = 30

    async def capture_output(
        self,
        output_dir: str,
        platform: str,
    ) -> List[dict]:
        output_path = await self._find_output_file(output_dir, platform)

        if not output_path:
            raise FileNotFoundError(
                f"未找到MediaCrawler输出文件：{output_dir}/{platform}/jsonl/"
            )

        results = []
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return self._deduplicate(results)

    async def _find_output_file(self, output_dir: str, platform: str) -> Optional[str]:
        # MediaCrawler saves to: {SAVE_DATA_PATH}/{platform}/jsonl/search_notes_{date}.jsonl
        search_dir = Path(output_dir) / platform / "jsonl"
        pattern = str(search_dir / "search_contents_*.jsonl")

        for _ in range(self.wait_timeout):
            matches = glob.glob(pattern)
            if matches:
                # Return the most recent file (sorted by date in filename)
                matches.sort(reverse=True)
                return matches[0]
            await asyncio.sleep(1)

        return None

    def _deduplicate(self, results: List[dict]) -> List[dict]:
        seen = set()
        unique_results = []
        for item in results:
            source_url = item.get("note_url") or item.get("note_id") or item.get("id")
            if source_url and source_url not in seen:
                seen.add(source_url)
                unique_results.append(item)
        return unique_results
