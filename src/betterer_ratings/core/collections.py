from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, Sequence


def merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def chunks(values: Sequence[int], size: int) -> Iterable[Sequence[int]]:
    for i in range(0, len(values), size):
        yield values[i : i + size]
