from __future__ import annotations

import sqlite3
from typing import Any, Optional

from betterer_ratings.core.clock import now_epoch
from betterer_ratings.core.parsing import parse_int
from betterer_ratings.infra.db import state_repo as db_state_repo


class LocalDatabaseStateMixin:
    conn: sqlite3.Connection

    def get_state_int(self, key: str, default: int) -> int:
        return db_state_repo.get_state_int(
            self.conn,
            key,
            default,
            parse_int_fn=parse_int,
        )

    def get_state(self, key: str) -> Optional[str]:
        return db_state_repo.get_state(self.conn, key)

    def set_state(self, key: str, value: Any) -> None:
        db_state_repo.set_state(self.conn, key, value)

    def delete_state(self, key: str) -> None:
        db_state_repo.delete_state(self.conn, key)

    def get_service_state(self, service: str) -> Optional[sqlite3.Row]:
        return db_state_repo.get_service_state(self.conn, service)

    def update_service_state(
        self,
        service: str,
        paused_until: Optional[int] = None,
        pause_reason: Optional[str] = None,
        rate_limit: Optional[int] = None,
        rate_remaining: Optional[int] = None,
        rate_reset: Optional[int] = None,
        last_status: Optional[int] = None,
    ) -> None:
        db_state_repo.update_service_state(
            self.conn,
            service=service,
            now_epoch_fn=now_epoch,
            paused_until=paused_until,
            pause_reason=pause_reason,
            rate_limit=rate_limit,
            rate_remaining=rate_remaining,
            rate_reset=rate_reset,
            last_status=last_status,
        )
