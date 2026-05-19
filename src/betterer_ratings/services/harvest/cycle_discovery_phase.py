from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from betterer_ratings.core.clock import format_duration
from betterer_ratings.services.harvest import cycle_helpers as harvest_cycle_helpers


async def run_discovery_phase(
    *,
    harvester: Any,
    stop_event: asyncio.Event,
    logger: Any,
    now_epoch_fn: Callable[[], int],
    local_day_key_fn: Callable[..., str],
    harvest_cycle_result_cls: Any,
) -> Tuple[
    List[Any],
    Dict[str, Dict[str, int]],
    int,
    Dict[str, int],
    str,
    Optional[Any],
]:
    self = harvester
    now_ts = now_epoch_fn()
    day_key = local_day_key_fn(now_ts)

    logger.debug("[Harvester] Cycle start: collecting local due candidates.")
    local_candidates, local_stats, local_interrupted = await self._collect_local_candidates(
        stop_event,
        day_key=day_key,
    )
    if stop_event.is_set() or local_interrupted:
        logger.info("[Harvester] Stop requested during local refresh selection.")
        return (
            local_candidates,
            {},
            0,
            local_stats,
            day_key,
            harvest_cycle_result_cls(
                selected_candidates=len(local_candidates),
                tmdb_list_request_errors=0,
                mdblist_request_failures=0,
                interrupted=True,
            ),
        )

    source_candidates: List[Any] = []
    source_stats: Dict[str, Dict[str, int]] = {}
    tmdb_list_request_errors = 0
    source_due = self._source_scan_due(now_ts)
    if source_due:
        source_names = ", ".join(source.name for source in self.scan_sources)
        logger.info("[Harvester] Source scan due: scanning sources=%s.", source_names)
        source_candidates, source_stats, source_interrupted = await self._collect_source_candidates(
            stop_event
        )
        tmdb_list_request_errors = sum(int(stat.get("errors") or 0) for stat in source_stats.values())
        if not source_interrupted and not stop_event.is_set():
            self.db.set_state(self._source_scan_last_run_key, now_epoch_fn())
        if source_interrupted or stop_event.is_set():
            logger.info("[Harvester] Stop requested during source scan.")
            return (
                harvest_cycle_helpers.merge_unique_candidates(local_candidates, source_candidates),
                source_stats,
                tmdb_list_request_errors,
                local_stats,
                day_key,
                harvest_cycle_result_cls(
                    selected_candidates=len(local_candidates) + len(source_candidates),
                    tmdb_list_request_errors=tmdb_list_request_errors,
                    mdblist_request_failures=0,
                    interrupted=True,
                ),
            )

    candidates = harvest_cycle_helpers.merge_unique_candidates(local_candidates, source_candidates)
    if not candidates and not source_due:
        last_idle_log = max(0, int(getattr(self, "_title_idle_last_log_ts", 0) or 0))
        if last_idle_log <= 0 or now_ts - last_idle_log >= 3600:
            last_source_scan = max(0, self.db.get_state_int(self._source_scan_last_run_key, 0))
            next_source_scan_in = max(
                0,
                int(last_source_scan) + int(self.source_scan_interval_seconds) - now_ts,
            )
            logger.info(
                "[Harvester] Title discovery idle: next source scan in %s; local due failed=%s ttl=%s new=%s total=%s.",
                format_duration(next_source_scan_in),
                local_stats["due_failed"],
                local_stats["due_ttl"],
                local_stats["due_new"],
                local_stats["due_total"],
            )
            self._title_idle_last_log_ts = now_ts
    discovery_log = logger.info if candidates or source_due else logger.debug
    discovery_log(
        "[Harvester] Discovery selected %s candidate(s): local=%s source=%s source_due=%s.",
        len(candidates),
        len(local_candidates),
        len(source_candidates),
        int(source_due),
    )
    return candidates, source_stats, tmdb_list_request_errors, local_stats, day_key, None
