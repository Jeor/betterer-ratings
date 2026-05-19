from __future__ import annotations

import asyncio
from typing import Any


async def worker_loop(
    *,
    stop_event: asyncio.Event,
    db: Any,
    poll_seconds: float,
    now_epoch_fn: Any,
    submit_mapping_fn: Any,
    submit_rating_fn: Any,
    submit_episode_ratings_batch_fn: Any,
    episode_batch_size: int = 50,
) -> None:
    while not stop_event.is_set():
        did_work = False

        now_ts = now_epoch_fn()
        kind = db.next_due_queue_kind(now_ts)
        if kind == "mapping":
            mapping_row = db.claim_next_pending_mapping(now_ts)
            if mapping_row is None:
                continue
            did_work = True
            await submit_mapping_fn(mapping_row)
        elif kind == "rating":
            rating_row = db.claim_next_pending_rating(now_ts)
            if rating_row is None:
                continue
            did_work = True
            await submit_rating_fn(rating_row)
        elif kind == "episode_ratings":
            episode_rows = db.claim_next_pending_episode_ratings_batch(
                now_ts=now_ts,
                batch_size=episode_batch_size,
            )
            if not episode_rows:
                continue
            did_work = True
            await submit_episode_ratings_batch_fn(episode_rows)

        if not did_work:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=poll_seconds)
            except asyncio.TimeoutError:
                pass
