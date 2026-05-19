from __future__ import annotations

import sqlite3
from pathlib import Path


def test_copied_data_uses_betterer_ratings_database_name():
    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "data" / "db" / "betterer_ratings.sqlite3"
    old_db_path = repo_root / "data" / "db" / "mdblist_pmdb.sqlite3"

    assert db_path.exists()
    assert not old_db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        for table in ("titles", "ratings", "mappings", "episode_ratings", "state"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count > 0
    finally:
        conn.close()
