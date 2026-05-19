from __future__ import annotations

from datetime import datetime, timezone

from betterer_ratings.services.harvest.imdb_archive_refresh_refresh import (
    latest_imdb_archive_refresh_epoch,
)


def _epoch(iso_value: str) -> int:
    return int(datetime.fromisoformat(iso_value).replace(tzinfo=timezone.utc).timestamp())


def test_imdb_archive_daily_refresh_window_is_1300_utc_before_cutoff():
    assert latest_imdb_archive_refresh_epoch(_epoch("2026-05-19T12:59:59")) == _epoch(
        "2026-05-18T13:00:00"
    )


def test_imdb_archive_daily_refresh_window_is_1300_utc_after_cutoff():
    assert latest_imdb_archive_refresh_epoch(_epoch("2026-05-19T13:00:00")) == _epoch(
        "2026-05-19T13:00:00"
    )
