from __future__ import annotations

import asyncio
from typing import Any, Callable


async def run_harvester(
    *,
    harvester: Any,
    stop_event: asyncio.Event,
    logger: Any,
    now_epoch_fn: Callable[[], int],
) -> None:
    cycle_attempted = 0
    while not stop_event.is_set():
        cycle_start = now_epoch_fn()
        cycle_attempted += 1
        try:
            await harvester._run_cycle(stop_event)
        except Exception:
            logger.exception("[Harvester] Unexpected cycle failure")

        if stop_event.is_set():
            logger.info(
                "[Harvester] Stop requested; exiting after cycle %s.",
                cycle_attempted,
            )
            break

        elapsed = now_epoch_fn() - cycle_start
        sleep_for = max(1, harvester.cycle_sleep_seconds - elapsed)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=sleep_for)
        except asyncio.TimeoutError:
            pass
