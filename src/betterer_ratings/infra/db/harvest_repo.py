from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Sequence, Tuple


def harvest_reason_case_sql() -> str:
    return (
        "CASE "
        "WHEN TRIM(COALESCE(last_error, '')) <> '' "
        "     AND ("
        "            ? <= 0 "
        "            OR last_harvested_at IS NULL "
        "            OR ? - last_harvested_at >= ?"
        "         ) "
        "THEN 'failed' "
        "WHEN last_harvested_at IS NULL THEN 'new' "
        "WHEN last_harvested_at IS NOT NULL "
        "     AND ? - last_harvested_at >= ? "
        "THEN 'ttl' "
        "ELSE '' "
        "END"
    )


def harvest_reason_case_params(
    *,
    now_ts: int,
    ratings_ttl_seconds: int,
    failed_retry_seconds: int,
) -> Tuple[int, int, int, int, int]:
    failed_retry = max(0, int(failed_retry_seconds))
    return (
        failed_retry,
        int(now_ts),
        failed_retry,
        int(now_ts),
        max(1, int(ratings_ttl_seconds)),
    )


def local_due_counts(
    conn: sqlite3.Connection,
    *,
    now_ts: int,
    ratings_ttl_seconds: int,
    failed_retry_seconds: int = 0,
) -> Dict[str, int]:
    reason_case = harvest_reason_case_sql()
    case_params = harvest_reason_case_params(
        now_ts=now_ts,
        ratings_ttl_seconds=ratings_ttl_seconds,
        failed_retry_seconds=failed_retry_seconds,
    )
    rows = conn.execute(
        f"""
        SELECT harvest_reason, COUNT(*) AS c
        FROM (
            SELECT {reason_case} AS harvest_reason
            FROM titles
        )
        WHERE harvest_reason <> ''
        GROUP BY harvest_reason
        """,
        case_params,
    ).fetchall()

    counts = {"failed": 0, "new": 0, "ttl": 0}
    for row in rows:
        reason = str(row["harvest_reason"] or "").strip().lower()
        if reason in counts:
            counts[reason] = int((row["c"] if row else 0) or 0)

    return {
        "failed": counts["failed"],
        "new": counts["new"],
        "ttl": counts["ttl"],
        "total": counts["failed"] + counts["new"] + counts["ttl"],
    }


def title_key_set(conn: sqlite3.Connection) -> set[Tuple[str, int]]:
    rows = conn.execute("SELECT media_type, tmdb_id FROM titles").fetchall()
    return {(str(row["media_type"]), int(row["tmdb_id"])) for row in rows}


def title_has_imdb_mapping(
    conn: sqlite3.Connection,
    *,
    tmdb_id: int,
    media_type: str,
) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM titles
        WHERE tmdb_id = ?
          AND media_type = ?
          AND TRIM(COALESCE(imdb_id, '')) <> ''
        UNION ALL
        SELECT 1
        FROM mappings
        WHERE tmdb_id = ?
          AND media_type = ?
          AND id_type = 'imdb'
          AND TRIM(COALESCE(id_value, '')) <> ''
        LIMIT 1
        """,
        (int(tmdb_id), media_type, int(tmdb_id), media_type),
    ).fetchone()
    return row is not None


def select_local_due_titles(
    conn: sqlite3.Connection,
    *,
    now_ts: int,
    ratings_ttl_seconds: int,
    limit: int,
    failed_retry_seconds: int = 0,
    harvest_reason_order: Sequence[str],
) -> List[sqlite3.Row]:
    safe_limit = max(0, int(limit))
    if safe_limit <= 0:
        return []

    reasons = tuple(harvest_reason_order)

    reason_case = harvest_reason_case_sql()
    case_params = list(
        harvest_reason_case_params(
            now_ts=now_ts,
            ratings_ttl_seconds=ratings_ttl_seconds,
            failed_retry_seconds=failed_retry_seconds,
        )
    )
    reason_placeholders = ", ".join("?" for _ in reasons)
    params: List[Any] = case_params + list(reasons) + [safe_limit]
    return conn.execute(
        f"""
        SELECT
            tmdb_id,
            media_type,
            title,
            popularity,
            last_harvested_at,
            last_error,
            harvest_reason
        FROM (
            SELECT
                tmdb_id,
                media_type,
                title,
                popularity,
                last_harvested_at,
                last_error,
                {reason_case} AS harvest_reason
            FROM titles
        )
        WHERE harvest_reason IN ({reason_placeholders})
        ORDER BY
            CASE harvest_reason
                WHEN 'failed' THEN 0
                WHEN 'ttl' THEN 1
                WHEN 'new' THEN 2
                ELSE 3
            END,
            COALESCE(last_harvested_at, 0) ASC,
            media_type ASC,
            tmdb_id ASC
        LIMIT ?
        """,
        tuple(params),
    ).fetchall()
