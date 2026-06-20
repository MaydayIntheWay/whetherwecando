"""
MediaCrawler输出捕获器
从MediaCrawler生成的jsonl文件中读取爬取结果。
MediaCrawler输出路径: {save_path}/{platform}/jsonl/search_contents_{date}.jsonl

支持两种模式：
- capture_output(): 批处理模式，等子进程结束后一次性读取
- stream_output(): 流式模式，子进程边写边读，实现实时进度
"""
import asyncio
import glob
import json
import os
from pathlib import Path
from typing import List, Optional, AsyncIterator


class MediaCrawlerOutputCapture:
    def __init__(self):
        self.wait_timeout = 120

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

    async def stream_output(
        self,
        output_dir: str,
        platform: str,
        done_event: asyncio.Event,
    ) -> AsyncIterator[dict]:
        """
        流式读取 MediaCrawler 子进程正在写入的 JSONL 文件。

        子进程边爬边写，此方法边读边 yield，实现逐条实时进度。
        done_event 由调用方在子进程结束后设置，此方法读到文件末尾后会
        等待新行或 done_event。

        Yields:
            每一条 JSONL 行解析后的 dict（已去重）
        """
        file_path = await self._wait_for_file(output_dir, platform, done_event)
        if not file_path:
            print(f"[STREAM] 未找到 JSONL 文件: {output_dir}/{platform}/jsonl/search_contents_*.jsonl", flush=True)
            return
        print(f"[STREAM] 开始 tail 文件: {file_path}", flush=True)

        seen = set()
        line_count = 0
        yield_count = 0
        # 用 os.open + os.read 实现真正的 tail（避免 Python 缓冲和 EOF 锁定问题）
        fd = os.open(file_path, os.O_RDONLY | os.O_BINARY if hasattr(os, 'O_BINARY') else os.O_RDONLY)
        try:
            leftover = ""
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    if done_event.is_set():
                        break
                    await asyncio.sleep(0.3)
                    continue

                text = leftover + chunk.decode("utf-8", errors="ignore")
                lines = text.split("\n")
                # 最后一段可能是不完整的行，保留到下次
                leftover = lines.pop()

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    note_id = data.get("note_url") or data.get("note_id") or data.get("id") or data.get("content_id") or data.get("question_id")
                    line_count += 1
                    if not note_id:
                        print(f"[STREAM] 跳过无ID行 #{line_count}: keys={list(data.keys())[:5]}...", flush=True)
                        continue
                    if note_id in seen:
                        print(f"[STREAM] 跳过重复: {str(note_id)[:50]}", flush=True)
                        continue
                    seen.add(note_id)
                    yield_count += 1
                    yield data
            if yield_count == 0 and line_count > 0:
                print(f"[STREAM] 警告: 读取 {line_count} 行但 yield 0 条 (platform={platform})", flush=True)
            else:
                print(f"[STREAM] 结束: 读取 {line_count} 行, yield {yield_count} 条", flush=True)
        finally:
            os.close(fd)

    async def _wait_for_file(
        self, output_dir: str, platform: str, done_event: asyncio.Event
    ) -> Optional[str]:
        search_dir = Path(output_dir) / platform / "jsonl"
        pattern = str(search_dir / "search_contents_*.jsonl")

        print(f"[STREAM] 等待 JSONL 文件: {pattern} (最长 {self.wait_timeout}s)", flush=True)
        for i in range(self.wait_timeout):
            matches = glob.glob(pattern)
            if matches:
                matches.sort(reverse=True)
                print(f"[STREAM] 找到文件: {matches[0]} (耗时 {i+1}s)", flush=True)
                return matches[0]
            if done_event.is_set():
                print(f"[STREAM] 子进程已结束但未找到 JSONL 文件", flush=True)
                return None
            if i % 10 == 9:
                print(f"[STREAM] 仍在等待文件... ({i+1}s)", flush=True)
            await asyncio.sleep(1)

        print(f"[STREAM] 等待超时 ({self.wait_timeout}s) 未找到文件", flush=True)
        return None

    async def _find_output_file(self, output_dir: str, platform: str) -> Optional[str]:
        search_dir = Path(output_dir) / platform / "jsonl"
        pattern = str(search_dir / "search_contents_*.jsonl")

        for _ in range(self.wait_timeout):
            matches = glob.glob(pattern)
            if matches:
                matches.sort(reverse=True)
                return matches[0]
            await asyncio.sleep(1)

        return None

    def _deduplicate(self, results: List[dict]) -> List[dict]:
        seen = set()
        unique_results = []
        for item in results:
            source_url = item.get("note_url") or item.get("note_id") or item.get("id") or item.get("content_id") or item.get("question_id")
            if source_url and source_url not in seen:
                seen.add(source_url)
                unique_results.append(item)
        return unique_results
