from __future__ import annotations

import sqlite3
from typing import Any, Callable, Optional, cast


def get_state_int(
    conn: sqlite3.Connection,
    key: str,
    default: int,
    *,
    parse_int_fn: Callable[[Any], Optional[int]],
) -> int:
    row = conn.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    parsed = parse_int_fn(row["value"])
    return default if parsed is None else parsed


def get_state(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute(
        "SELECT value FROM state WHERE key = ?",
        (key,),
    ).fetchone()
    if row is None:
        return None
    return str(row["value"])


def set_state(conn: sqlite3.Connection, key: str, value: Any) -> None:
    with conn:
        conn.execute(
            """
            INSERT INTO state(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, str(value)),
        )


def delete_state(conn: sqlite3.Connection, key: str) -> None:
    with conn:
        conn.execute("DELETE FROM state WHERE key = ?", (key,))


def get_service_state(conn: sqlite3.Connection, service: str) -> Optional[sqlite3.Row]:
    return cast(Optional[sqlite3.Row], conn.execute(
        "SELECT * FROM service_state WHERE service = ?",
        (service,),
    ).fetchone())


def update_service_state(
    conn: sqlite3.Connection,
    *,
    service: str,
    now_epoch_fn: Callable[[], int],
    paused_until: Optional[int] = None,
    pause_reason: Optional[str] = None,
    rate_limit: Optional[int] = None,
    rate_remaining: Optional[int] = None,
    rate_reset: Optional[int] = None,
    last_status: Optional[int] = None,
) -> None:
    now_ts = now_epoch_fn()
    with conn:
        conn.execute(
            """
            INSERT INTO service_state(
                service,
                paused_until,
                pause_reason,
                rate_limit,
                rate_remaining,
                rate_reset,
                last_status,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(service) DO UPDATE SET
                paused_until=COALESCE(excluded.paused_until, service_state.paused_until),
                pause_reason=COALESCE(excluded.pause_reason, service_state.pause_reason),
                rate_limit=COALESCE(excluded.rate_limit, service_state.rate_limit),
                rate_remaining=COALESCE(excluded.rate_remaining, service_state.rate_remaining),
                rate_reset=COALESCE(excluded.rate_reset, service_state.rate_reset),
                last_status=COALESCE(excluded.last_status, service_state.last_status),
                updated_at=excluded.updated_at
            """,
            (
                service,
                paused_until,
                pause_reason,
                rate_limit,
                rate_remaining,
                rate_reset,
                last_status,
                now_ts,
            ),
        )
