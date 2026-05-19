from __future__ import annotations

import datetime as dt

from betterer_ratings.services.submit.runner import format_queue_status, submission_log_extra


def test_submitter_queue_status_summary_includes_all_work_types():
    message = format_queue_status(
        {
            "ratings_pending": 1,
            "ratings_in_flight": 2,
            "ratings_failed": 3,
            "mappings_pending": 4,
            "mappings_in_flight": 5,
            "mappings_failed": 6,
            "episode_ratings_pending": 7,
            "episode_ratings_in_flight": 8,
            "episode_ratings_failed": 9,
        }
    )

    assert "ratings(pending=1 in_flight=2 failed=3)" in message
    assert "mappings(pending=4 in_flight=5 failed=6)" in message
    assert "episode_ratings(pending=7 in_flight=8 failed=9)" in message


def test_submission_summary_counts_today_and_database_totals(local_db):
    db = local_db
    day_start = int(dt.datetime(2026, 5, 19, tzinfo=dt.timezone.utc).timestamp())
    now_ts = day_start + 3600
    yesterday = day_start - 86400

    db.conn.executemany(
        """
        INSERT INTO ratings(
            tmdb_id, media_type, label, score, fetched_at, pmdb_status, pmdb_submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "movie", "IM", 80.0, yesterday, "submitted", yesterday),
            (2, "movie", "IM", 82.0, now_ts, "submitted", now_ts),
        ],
    )
    db.conn.executemany(
        """
        INSERT INTO mappings(
            tmdb_id, media_type, id_type, id_value, fetched_at, pmdb_status, pmdb_submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "movie", "imdb", "tt1", yesterday, "submitted", yesterday),
            (2, "movie", "imdb", "tt2", now_ts, "submitted", now_ts),
        ],
    )
    db.conn.executemany(
        """
        INSERT INTO episode_ratings(
            tmdb_id, media_type, season, episode, label, score, fetched_at, pmdb_status, pmdb_submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (10, "tv", 1, 1, "IM", 90.0, yesterday, "submitted", yesterday),
            (10, "tv", 1, 2, "IM", 91.0, now_ts, "submitted", now_ts),
        ],
    )

    summary = db.submission_summary(now_ts)

    assert summary["ratings_today"] == 1
    assert summary["mappings_today"] == 1
    assert summary["episode_ratings_today"] == 1
    assert summary["ratings_total"] == 2
    assert summary["mappings_total"] == 2
    assert summary["episode_ratings_total"] == 2


def test_submission_log_extra_omits_epoch_day_bounds():
    extra = submission_log_extra(
        {
            "day": "2026-05-19",
            "day_start_ts": 1779134400,
            "day_end_ts": 1779220800,
            "ratings_today": 10,
            "mappings_today": 11,
            "episode_ratings_today": 12,
            "ratings_total": 100,
            "mappings_total": 101,
            "episode_ratings_total": 102,
            "titles_total": 103,
        }
    )

    assert extra["event"] == "submission.summary"
    assert "day_start_ts" not in extra
    assert "day_end_ts" not in extra
