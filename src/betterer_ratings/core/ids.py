from __future__ import annotations

import re
from typing import Any, Optional

IMDB_TITLE_ID_RE = re.compile(r"^tt[0-9]+$")


def is_valid_imdb_title_id(value: Any) -> bool:
    if value is None:
        return False
    return IMDB_TITLE_ID_RE.match(str(value).strip()) is not None


def normalize_imdb_title_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None
    return candidate if is_valid_imdb_title_id(candidate) else None


def imdb_title_type_to_media_type(title_type: str) -> Optional[str]:
    lowered = str(title_type or "").strip().lower()
    if lowered in {"movie", "tvmovie"}:
        return "movie"
    if lowered in {"tvseries", "tvminiseries"}:
        return "tv"
    return None
