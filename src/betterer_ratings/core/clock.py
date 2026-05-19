from __future__ import annotations

import datetime as dt
import time
from typing import Optional, Tuple


def now_epoch() -> int:
    return int(time.time())


def local_day_key(ts: Optional[int] = None) -> str:
    epoch = now_epoch() if ts is None else int(ts)
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).astimezone().strftime("%Y-%m-%d")


def local_day_bounds(ts: Optional[int] = None) -> Tuple[str, int, int]:
    epoch = now_epoch() if ts is None else int(ts)
    local_now = dt.datetime.fromtimestamp(epoch, dt.timezone.utc).astimezone()
    start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + dt.timedelta(days=1)
    return start.strftime("%Y-%m-%d"), int(start.timestamp()), int(end.timestamp())


def to_iso(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone().strftime("%d-%m-%y %H:%M:%S")


def to_log_time(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def format_duration(seconds: int) -> str:
    remaining = max(0, int(seconds))
    days, remaining = divmod(remaining, 86400)
    hours, remaining = divmod(remaining, 3600)
    minutes, secs = divmod(remaining, 60)
    if days:
        return f"{days}d {hours}h" if hours else f"{days}d"
    if hours:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    if minutes:
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    return f"{secs}s"
