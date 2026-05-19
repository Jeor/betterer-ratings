from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Mapping

from betterer_ratings.config.schema import AppConfig, ConfigValidationError


class ConfigLayoutError(ConfigValidationError):
    pass


def parse_toml(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")

    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigLayoutError(f"Invalid TOML format in {path}: {exc}") from exc

    if not isinstance(payload, Mapping):
        raise ConfigLayoutError("Config root must be a TOML table")

    return payload


def load_config(path: Path) -> AppConfig:
    return AppConfig.from_mapping(parse_toml(path))
