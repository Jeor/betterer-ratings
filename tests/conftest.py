import copy
import datetime as dt
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tests import support as m


def _toml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _toml_quote(value)
    if isinstance(value, Mapping):
        parts = [f"{key} = {_toml_value(item)}" for key, item in value.items()]
        return "{ " + ", ".join(parts) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"Unsupported TOML value type: {type(value)!r}")


def _mapping_to_toml(payload: Mapping[str, Any]) -> str:
    lines: list[str] = []
    for section, section_value in payload.items():
        if isinstance(section_value, Mapping):
            lines.append(f"[{section}]")
            for key, value in section_value.items():
                lines.append(f"{key} = {_toml_value(value)}")
            lines.append("")
        else:
            lines.append(f"{section} = {_toml_value(section_value)}")
    return "\n".join(lines).rstrip() + "\n"


@pytest.fixture
def local_db(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    db = m.LocalDatabase(db_path)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def write_config(tmp_path):
    def _write(payload):
        config_path = tmp_path / "config.toml"
        if isinstance(payload, str):
            config_path.write_text(payload, encoding="utf-8")
            return config_path

        config_path.write_text(_mapping_to_toml(payload), encoding="utf-8")
        return config_path

    return _write


@pytest.fixture
def base_valid_config():
    config = copy.deepcopy(m.DEFAULT_CONFIG)
    config["api_keys"]["tmdb"] = "tmdb-key"
    config["api_keys"]["mdblist"] = "mdblist-key"
    config["api_keys"]["pmdb"] = "pmdb-key"
    return config


@pytest.fixture
def freeze_utc_now(monkeypatch):
    def _freeze(epoch_seconds: int):
        fixed = dt.datetime.fromtimestamp(epoch_seconds, dt.timezone.utc)

        class FrozenDateTime(dt.datetime):
            @classmethod
            def now(_cls, tz=None):
                if tz is None:
                    return fixed.replace(tzinfo=None)
                return fixed.astimezone(tz)

        monkeypatch.setattr(m.dt, "datetime", FrozenDateTime)
        return fixed

    return _freeze
