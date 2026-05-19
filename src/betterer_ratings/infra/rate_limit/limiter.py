from __future__ import annotations

import asyncio
import time
from collections import deque


class AsyncWindowLimiter:
    """Simple async sliding-window limiter."""

    def __init__(self, max_requests: int, period_seconds: float, name: str):
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self.name = name
        self._events: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                while self._events and now - self._events[0] >= self.period_seconds:
                    self._events.popleft()

                if len(self._events) < self.max_requests:
                    self._events.append(now)
                    return

                wait_for = self.period_seconds - (now - self._events[0])
                wait_for = max(0.001, wait_for)

            await asyncio.sleep(wait_for)
