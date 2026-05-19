from __future__ import annotations

import gzip
import shutil
from pathlib import Path
from typing import Any, Callable, Optional

import httpx

from betterer_ratings.core.clock import format_duration


def safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except Exception:
        return


def read_imdb_update_marker_epoch(
    *,
    marker_path: Path,
    parse_int_fn: Callable[[Any], Optional[int]],
) -> Optional[int]:
    try:
        raw = marker_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except Exception:
        return None
    parsed = parse_int_fn(raw)
    if parsed is None or parsed <= 0:
        return None
    return int(parsed)


def write_imdb_update_marker_epoch(
    *,
    marker_path: Path,
    epoch_seconds: int,
    safe_unlink_fn: Callable[[Path], None] = safe_unlink,
) -> None:
    safe_epoch = max(1, int(epoch_seconds))
    tmp_path = marker_path.parent / (f".{marker_path.name}.tmp")
    try:
        tmp_path.write_text(str(safe_epoch), encoding="utf-8")
        tmp_path.replace(marker_path)
    except Exception:
        safe_unlink_fn(tmp_path)


def file_timestamp_epoch(path: Path) -> Optional[int]:
    try:
        stat_result = path.stat()
    except Exception:
        return None
    timestamp_value = getattr(stat_result, "st_mtime", None)
    if timestamp_value is None:
        return None
    try:
        timestamp_int = int(timestamp_value)
    except (TypeError, ValueError):
        return None
    return timestamp_int if timestamp_int > 0 else None


def download_and_extract_imdb_dataset(
    *,
    dataset_name: str,
    url: str,
    gz_tmp_path: Path,
    tsv_tmp_path: Path,
    timeout_seconds: int,
) -> None:
    with httpx.stream("GET", url, timeout=timeout_seconds, follow_redirects=True) as resp:
        resp.raise_for_status()
        with gz_tmp_path.open("wb") as gz_out:
            for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                if chunk:
                    gz_out.write(chunk)

    with gzip.open(gz_tmp_path, "rb") as gz_in, tsv_tmp_path.open("wb") as tsv_out:
        shutil.copyfileobj(gz_in, tsv_out, length=1024 * 1024)

    if tsv_tmp_path.stat().st_size <= 0:
        raise ValueError(f"Downloaded IMDb dataset is empty after extraction: {dataset_name}")


def extract_local_imdb_gz_if_needed(
    *,
    dataset_name: str,
    archive_dir: Path,
    now_ts: int,
    max_age_seconds: int,
    logger: Any,
    file_timestamp_epoch_fn: Callable[[Path], Optional[int]] = file_timestamp_epoch,
    safe_unlink_fn: Callable[[Path], None] = safe_unlink,
) -> bool:
    tsv_path = archive_dir / dataset_name
    if tsv_path.exists():
        return False
    gz_path = archive_dir / f"{dataset_name}.gz"
    if not gz_path.exists():
        return False
    file_timestamp = file_timestamp_epoch_fn(gz_path)
    if file_timestamp is None:
        logger.info(
            "[IMDbArchive] Skipping local %s extraction: .gz timestamp unavailable.",
            dataset_name,
        )
        return False
    age_seconds = max(0, int(now_ts - file_timestamp))
    if age_seconds > max_age_seconds:
        logger.info(
            "[IMDbArchive] Skipping local %s extraction: .gz is stale (%s old > %s).",
            dataset_name,
            format_duration(age_seconds),
            format_duration(max_age_seconds),
        )
        return False

    tsv_tmp_path = archive_dir / f".{dataset_name}.extract.tmp"
    safe_unlink_fn(tsv_tmp_path)
    try:
        with gzip.open(gz_path, "rb") as gz_in, tsv_tmp_path.open("wb") as tsv_out:
            shutil.copyfileobj(gz_in, tsv_out, length=1024 * 1024)
        if tsv_tmp_path.stat().st_size <= 0:
            raise ValueError(f"Extracted IMDb TSV is empty: {dataset_name}")
        tsv_tmp_path.replace(tsv_path)
        # Keep archive directory tidy: remove consumed .gz after extraction.
        safe_unlink_fn(gz_path)
        logger.info(
            "[IMDbArchive] Extracted local dataset %s from %s",
            dataset_name,
            gz_path.name,
        )
        return True
    except Exception:
        safe_unlink_fn(tsv_tmp_path)
        return False
