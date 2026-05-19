from __future__ import annotations

from typing import Any, Dict, Optional

from betterer_ratings.domain.models import TMDBSource


def build_source(entry: Dict[str, Any]) -> TMDBSource:
    name = str(entry.get("name", "")).strip().lower().lstrip("/")
    endpoint = f"/{name}"
    media_type_hint: Optional[str] = None
    if name.startswith("movie/") or name.startswith("trending/movie/"):
        media_type_hint = "movie"
    elif name.startswith("tv/") or name.startswith("trending/tv/"):
        media_type_hint = "tv"
    elif name.startswith("trending/all/"):
        media_type_hint = None
    else:
        raise ValueError(f"Unsupported TMDB source name: {name}")

    max_pages = max(1, min(500, int(entry.get("max_pages", 500))))
    return TMDBSource(
        name=name,
        endpoint=endpoint,
        media_type_hint=media_type_hint,
        max_pages=max_pages,
    )
