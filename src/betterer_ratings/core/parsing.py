from __future__ import annotations

from typing import Any, Optional

NULLISH_TEXT = {"none", "null", "n/a"}


def parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        value_str = str(value).strip()
        if value_str and value_str.lower() not in NULLISH_TEXT:
            return value_str
    return None
