from __future__ import annotations

import json
from typing import Any, Callable


def run_one_time_retry_storm_cleanup(
    *,
    db: Any,
    max_retry_attempts: int,
    retry_storm_cleanup_key: str,
    now_epoch_fn: Callable[[], int],
    logger: Any,
) -> None:
    cleanup_key = f"{retry_storm_cleanup_key}:{max_retry_attempts}"
    existing = db.get_state(cleanup_key)
    if existing:
        return
    affected = db.cleanup_retry_storm_rows(max_retry_attempts)
    payload = {
        "ran_at": now_epoch_fn(),
        "max_retry_attempts": max_retry_attempts,
        "ratings_failed": int(affected["ratings"]),
        "mappings_failed": int(affected["mappings"]),
    }
    db.set_state(cleanup_key, json.dumps(payload, separators=(",", ":")))
    if affected["ratings"] > 0 or affected["mappings"] > 0:
        logger.warning(
            "[Submitter] One-time retry-storm cleanup marked rows failed (ratings=%s mappings=%s, threshold=%s).",
            affected["ratings"],
            affected["mappings"],
            max_retry_attempts,
        )
    else:
        logger.info("[Submitter] One-time retry-storm cleanup: no rows matched.")
