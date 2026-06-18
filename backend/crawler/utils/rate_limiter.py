"""
请求频率控制器
"""
import asyncio
import random
from typing import Optional


class RateLimiter:
    def __init__(self, min_interval: float = 2.0, max_interval: float = 5.0):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self._last_request_time: Optional[float] = None
    
    async def wait(self):
        interval = random.uniform(self.min_interval, self.max_interval)
        await asyncio.sleep(interval)
        self._last_request_time = asyncio.get_event_loop().time()
    
    def get_random_interval(self) -> float:
        return random.uniform(self.min_interval, self.max_interval)


rate_limiter = RateLimiter()
