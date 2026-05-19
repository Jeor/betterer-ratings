from __future__ import annotations

# ruff: noqa: F401
import betterer_ratings.constants as constants
from betterer_ratings.config.loader import load_config
from betterer_ratings.config.schema import ConfigValidationError
from betterer_ratings.core import clock as _clock
from betterer_ratings.core.collections import chunks, merge_dict
from betterer_ratings.core.ids import (
    imdb_title_type_to_media_type,
    is_valid_imdb_title_id,
    normalize_imdb_title_id,
)
from betterer_ratings.core.mappings import extract_mappings
from betterer_ratings.core.network import is_network_unavailable_error
from betterer_ratings.core.parsing import first_non_empty, parse_int
from betterer_ratings.core.retry import dt, parse_retry_after
from betterer_ratings.core.scoring import (
    clamp_0_100,
    parse_mdblist_ratings,
    parse_tmdb_vote_average,
    parse_value_and_scale,
    scale_to_100,
    score_to_tenths,
)
from betterer_ratings.core.urls import sanitize_url_for_logs
from betterer_ratings.domain.models import (
    APIResponse,
    IMDbEpisodeArchiveCandidate,
    PMDBSubmitResult,
)
from betterer_ratings.infra.db.local_database import LocalDatabase
from betterer_ratings.providers.pmdb_client import PMDBClient
from betterer_ratings.providers.tmdb_client import TMDBClient

DEFAULT_CONFIG = constants.DEFAULT_CONFIG


def now_epoch() -> int:
    return _clock.now_epoch()


def local_day_key(ts: int | None = None) -> str:
    epoch = now_epoch() if ts is None else int(ts)
    return _clock.local_day_key(epoch)


def to_iso(ts: int) -> str:
    return _clock.to_iso(ts)
