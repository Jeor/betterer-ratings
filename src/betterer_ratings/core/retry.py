from __future__ import annotations

import datetime as dt
import email.utils
from typing import Optional

from .parsing import parse_int


def parse_retry_after(value: Optional[str], default_seconds: int = 5) -> int:
    if not value:
        return default_seconds

    stripped = value.strip()
    as_int = parse_int(stripped)
    if as_int is not None:
        return max(1, as_int)

    try:
        dt_value = email.utils.parsedate_to_datetime(stripped)
        if dt_value.tzinfo is None:
            dt_value = dt_value.replace(tzinfo=dt.timezone.utc)
        delta = int((dt_value - dt.datetime.now(dt.timezone.utc)).total_seconds())
        return max(1, delta)
    except Exception:
        return default_seconds
