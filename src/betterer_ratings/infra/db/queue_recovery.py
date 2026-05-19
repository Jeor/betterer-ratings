from __future__ import annotations

import sqlite3
from typing import Callable, Dict


def recover_in_flight_rows(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute(
            """
            UPDATE ratings
            SET pmdb_status = 'retry',
                pmdb_retry_after = 0,
                pmdb_claimed_at = NULL,
                pmdb_last_error = COALESCE(pmdb_last_error, 'Recovered from in_flight')
            WHERE pmdb_status = 'in_flight'
            """
        )
        conn.execute(
            """
            UPDATE mappings
            SET pmdb_status = 'retry',
                pmdb_retry_after = 0,
                pmdb_claimed_at = NULL,
                pmdb_last_error = COALESCE(pmdb_last_error, 'Recovered from in_flight')
            WHERE pmdb_status = 'in_flight'
            """
        )
        conn.execute(
            """
            UPDATE episode_ratings
            SET pmdb_status = 'retry',
                pmdb_retry_after = 0,
                pmdb_claimed_at = NULL,
                pmdb_last_error = COALESCE(pmdb_last_error, 'Recovered from in_flight')
            WHERE pmdb_status = 'in_flight'
            """
        )


def recover_stale_in_flight_rows(
    conn: sqlite3.Connection,
    *,
    lease_seconds: int,
    now_epoch_fn: Callable[[], int],
) -> Dict[str, int]:
    lease = max(30, int(lease_seconds))
    cutoff = now_epoch_fn() - lease
    ratings_count_row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM ratings
        WHERE pmdb_status = 'in_flight'
          AND COALESCE(pmdb_claimed_at, 0) <= ?
        """,
        (cutoff,),
    ).fetchone()
    episode_ratings_count_row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM episode_ratings
        WHERE pmdb_status = 'in_flight'
          AND COALESCE(pmdb_claimed_at, 0) <= ?
        """,
        (cutoff,),
    ).fetchone()
    mappings_count_row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM mappings
        WHERE pmdb_status = 'in_flight'
          AND COALESCE(pmdb_claimed_at, 0) <= ?
        """,
        (cutoff,),
    ).fetchone()
    with conn:
        conn.execute(
            """
            UPDATE ratings
            SET pmdb_status = 'retry',
                pmdb_retry_after = 0,
                pmdb_claimed_at = NULL,
                pmdb_last_error = COALESCE(pmdb_last_error, 'Recovered stale in_flight lease')
            WHERE pmdb_status = 'in_flight'
              AND COALESCE(pmdb_claimed_at, 0) <= ?
            """,
            (cutoff,),
        )
        conn.execute(
            """
            UPDATE episode_ratings
            SET pmdb_status = 'retry',
                pmdb_retry_after = 0,
                pmdb_claimed_at = NULL,
                pmdb_last_error = COALESCE(pmdb_last_error, 'Recovered stale in_flight lease')
            WHERE pmdb_status = 'in_flight'
              AND COALESCE(pmdb_claimed_at, 0) <= ?
            """,
            (cutoff,),
        )
        conn.execute(
            """
            UPDATE mappings
            SET pmdb_status = 'retry',
                pmdb_retry_after = 0,
                pmdb_claimed_at = NULL,
                pmdb_last_error = COALESCE(pmdb_last_error, 'Recovered stale in_flight lease')
            WHERE pmdb_status = 'in_flight'
              AND COALESCE(pmdb_claimed_at, 0) <= ?
            """,
            (cutoff,),
        )
    return {
        "ratings": int(ratings_count_row["c"] if ratings_count_row else 0),
        "episode_ratings": int(episode_ratings_count_row["c"] if episode_ratings_count_row else 0),
        "mappings": int(mappings_count_row["c"] if mappings_count_row else 0),
    }


def cleanup_retry_storm_rows(
    conn: sqlite3.Connection,
    *,
    max_attempts: int,
) -> Dict[str, int]:
    threshold = max(1, int(max_attempts))
    ratings_error = (
        '{"service":"pmdb","endpoint":"/api/external/ratings","status":500,'
        '"code":"auto_failed_max_attempts","retryable":false,'
        '"message":"Auto-failed retry storm row after max retry attempts '
        '(likely permanent create conflict)."}'
    )
    mappings_error = (
        '{"service":"pmdb","endpoint":"/api/external/mappings","status":500,'
        '"code":"auto_failed_max_attempts","retryable":false,'
        '"message":"Auto-failed retry storm row after max retry attempts '
        '(likely permanent create conflict)."}'
    )
    ratings_count_row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM ratings
        WHERE pmdb_status = 'retry'
          AND pmdb_attempts >= ?
          AND COALESCE(pmdb_last_error, '') LIKE '%"status":500%'
          AND COALESCE(pmdb_last_error, '') LIKE '%Failed to create rating%'
        """,
        (threshold,),
    ).fetchone()
    mappings_count_row = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM mappings
        WHERE pmdb_status = 'retry'
          AND pmdb_attempts >= ?
          AND COALESCE(pmdb_last_error, '') LIKE '%"status":500%'
          AND COALESCE(pmdb_last_error, '') LIKE '%Failed to create ID mapping%'
        """,
        (threshold,),
    ).fetchone()
    with conn:
        conn.execute(
            """
            UPDATE ratings
            SET pmdb_status = 'failed',
                pmdb_claimed_at = NULL,
                pmdb_last_error = ?
            WHERE pmdb_status = 'retry'
              AND pmdb_attempts >= ?
              AND COALESCE(pmdb_last_error, '') LIKE '%"status":500%'
              AND COALESCE(pmdb_last_error, '') LIKE '%Failed to create rating%'
            """,
            (ratings_error, threshold),
        )
        conn.execute(
            """
            UPDATE mappings
            SET pmdb_status = 'failed',
                pmdb_claimed_at = NULL,
                pmdb_last_error = ?
            WHERE pmdb_status = 'retry'
              AND pmdb_attempts >= ?
              AND COALESCE(pmdb_last_error, '') LIKE '%"status":500%'
              AND COALESCE(pmdb_last_error, '') LIKE '%Failed to create ID mapping%'
            """,
            (mappings_error, threshold),
        )
    return {
        "ratings": int(ratings_count_row["c"] if ratings_count_row else 0),
        "mappings": int(mappings_count_row["c"] if mappings_count_row else 0),
    }
