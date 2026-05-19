from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Sequence, Tuple


async def run_tmdb_details_phase(
    *,
    harvester: Any,
    stop_event: asyncio.Event,
    logger: Any,
    candidates: Sequence[Any],
    source_stats: Dict[str, Dict[str, int]],
    tmdb_list_request_errors: int,
    local_stats: Dict[str, int],
    harvest_cycle_result_cls: Any,
) -> Tuple[Optional[Dict[Tuple[str, int], Optional[Dict[str, Any]]]], Optional[Any]]:
    del source_stats, local_stats
    self = harvester
    logger.info("[Harvester] Fetching TMDB details for %s candidate(s).", len(candidates))
    tmdb_details, details_interrupted = await self._fetch_tmdb_details(candidates, stop_event)
    if details_interrupted or stop_event.is_set():
        logger.info("[Harvester] Stop requested during TMDB details.")
        return (
            None,
            harvest_cycle_result_cls(
                selected_candidates=len(candidates),
                tmdb_list_request_errors=tmdb_list_request_errors,
                mdblist_request_failures=0,
                interrupted=True,
            ),
        )

    logger.info("[Harvester] TMDB details complete. Starting MDBList enrichment.")
    return (tmdb_details, None)
