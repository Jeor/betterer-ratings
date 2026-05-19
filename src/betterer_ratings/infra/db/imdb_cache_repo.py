from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Sequence, Tuple

from betterer_ratings.core.ids import normalize_imdb_title_id
from betterer_ratings.core.parsing import parse_int


class IMDbTMDBCache:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS imdb_tmdb_cache (
                    imdb_id TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    tmdb_id INTEGER NOT NULL,
                    title TEXT,
                    popularity REAL,
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY (imdb_id, media_type)
                )
                """
            )
            self.conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_imdb_tmdb_cache_tmdb
                ON imdb_tmdb_cache (tmdb_id, media_type)
                """
            )

    def get(self, imdb_id: str, media_type: str) -> Optional[Tuple[int, str, float]]:
        normalized_imdb = normalize_imdb_title_id(imdb_id)
        normalized_media = str(media_type or "").strip().lower()
        if not normalized_imdb or normalized_media not in {"movie", "tv"}:
            return None
        row = self.conn.execute(
            """
            SELECT tmdb_id, title, popularity
            FROM imdb_tmdb_cache
            WHERE imdb_id = ? AND media_type = ?
            """,
            (normalized_imdb, normalized_media),
        ).fetchone()
        if row is None:
            return None
        tmdb_id = parse_int(row["tmdb_id"])
        if tmdb_id is None:
            return None
        title = str(row["title"] or "").strip()
        try:
            popularity = float(row["popularity"] or 0.0)
        except (TypeError, ValueError):
            popularity = 0.0
        return tmdb_id, title, popularity

    def _normalize_upsert_row(
        self,
        *,
        imdb_id: str,
        media_type: str,
        tmdb_id: int,
        title: str,
        popularity: float,
        updated_at: int,
    ) -> Optional[Tuple[str, str, int, str, float, int]]:
        normalized_imdb = normalize_imdb_title_id(imdb_id)
        normalized_media = str(media_type or "").strip().lower()
        if (
            not normalized_imdb
            or normalized_media not in {"movie", "tv"}
            or parse_int(tmdb_id) is None
        ):
            return None
        return (
            normalized_imdb,
            normalized_media,
            int(tmdb_id),
            str(title or "").strip(),
            float(popularity or 0.0),
            int(updated_at),
        )

    def upsert_many(self, rows: Sequence[Tuple[str, str, int, str, float, int]]) -> int:
        normalized_rows = []
        for imdb_id, media_type, tmdb_id, title, popularity, updated_at in rows:
            normalized = self._normalize_upsert_row(
                imdb_id=imdb_id,
                media_type=media_type,
                tmdb_id=tmdb_id,
                title=title,
                popularity=popularity,
                updated_at=updated_at,
            )
            if normalized is None:
                continue
            normalized_rows.append(normalized)
        if not normalized_rows:
            return 0

        with self.conn:
            self.conn.executemany(
                """
                INSERT INTO imdb_tmdb_cache(
                    imdb_id,
                    media_type,
                    tmdb_id,
                    title,
                    popularity,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(imdb_id, media_type) DO UPDATE SET
                    tmdb_id = excluded.tmdb_id,
                    title = excluded.title,
                    popularity = excluded.popularity,
                    updated_at = excluded.updated_at
                """,
                normalized_rows,
            )
        return len(normalized_rows)

    def upsert(
        self,
        *,
        imdb_id: str,
        media_type: str,
        tmdb_id: int,
        title: str,
        popularity: float,
        updated_at: int,
    ) -> None:
        self.upsert_many(
            [
                (
                    imdb_id,
                    media_type,
                    int(tmdb_id),
                    str(title or "").strip(),
                    float(popularity or 0.0),
                    int(updated_at),
                )
            ]
        )
