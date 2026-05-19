from __future__ import annotations

from typing import Any, Dict, Optional

from .ids import normalize_imdb_title_id
from .parsing import first_non_empty


def extract_mappings(
    media_type: str,
    tmdb_details: Optional[Dict[str, Any]],
    mdblist_item: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    del media_type  # Reserved for future mapping rules by media kind.

    mappings: Dict[str, str] = {}

    tmdb_external = {}
    if tmdb_details and isinstance(tmdb_details, dict):
        external_ids = tmdb_details.get("external_ids")
        if isinstance(external_ids, dict):
            tmdb_external = external_ids

    md_ids = {}
    if mdblist_item and isinstance(mdblist_item, dict):
        ids_block = mdblist_item.get("ids")
        if isinstance(ids_block, dict):
            md_ids = ids_block

    imdb_id = first_non_empty(
        tmdb_external.get("imdb_id"),
        (tmdb_details or {}).get("imdb_id"),
        md_ids.get("imdb"),
        (mdblist_item or {}).get("imdb_id"),
        (mdblist_item or {}).get("imdbid"),
    )
    normalized_imdb = normalize_imdb_title_id(imdb_id)
    if normalized_imdb:
        mappings["imdb"] = normalized_imdb

    tvdb_id = first_non_empty(
        tmdb_external.get("tvdb_id"),
        md_ids.get("tvdb"),
        (mdblist_item or {}).get("tvdb_id"),
        (mdblist_item or {}).get("tvdbid"),
    )
    if tvdb_id:
        mappings["tvdb"] = tvdb_id

    trakt_id = first_non_empty(
        md_ids.get("trakt"),
        (mdblist_item or {}).get("trakt_id"),
        (mdblist_item or {}).get("traktid"),
    )
    if trakt_id:
        mappings["trakt"] = trakt_id

    mal_id = first_non_empty(
        md_ids.get("mal"),
        (mdblist_item or {}).get("mal_id"),
        (mdblist_item or {}).get("malid"),
        (mdblist_item or {}).get("myanimelist_id"),
    )
    if mal_id:
        mappings["mal"] = mal_id

    anilist_id = first_non_empty(
        md_ids.get("anilist"),
        (mdblist_item or {}).get("anilist_id"),
        (mdblist_item or {}).get("anilistid"),
    )
    if anilist_id:
        mappings["anilist"] = anilist_id

    anidb_id = first_non_empty(
        md_ids.get("anidb"),
        (mdblist_item or {}).get("anidb_id"),
        (mdblist_item or {}).get("anidbid"),
    )
    if anidb_id:
        mappings["anidb"] = anidb_id

    return mappings
