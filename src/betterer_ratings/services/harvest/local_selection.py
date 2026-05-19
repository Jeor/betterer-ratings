from __future__ import annotations

from typing import Any, Dict


def init_local_stats() -> Dict[str, int]:
    return {
        "due_total": 0,
        "due_failed": 0,
        "due_new": 0,
        "due_ttl": 0,
        "selected_total": 0,
        "selected_failed": 0,
        "selected_new": 0,
        "selected_ttl": 0,
    }


def local_due_counts(
    *,
    db: Any,
    now_ts: int,
    ratings_ttl_seconds: int,
    failed_retry_seconds: int,
) -> Dict[str, int]:
    return dict(db.local_due_counts(
        now_ts=now_ts,
        ratings_ttl_seconds=ratings_ttl_seconds,
        failed_retry_seconds=failed_retry_seconds,
    ))
