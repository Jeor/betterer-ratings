from __future__ import annotations

from typing import Any, List, Sequence, Set, Tuple


def merge_unique_candidates(*groups: Sequence[Any]) -> List[Any]:
    merged: List[Any] = []
    seen: Set[Tuple[str, int]] = set()
    for group in groups:
        for candidate in group:
            key = (candidate.media_type, candidate.tmdb_id)
            if key in seen:
                continue
            seen.add(key)
            merged.append(candidate)
    return merged
