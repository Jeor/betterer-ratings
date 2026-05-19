from __future__ import annotations

from betterer_ratings.core.clock import format_duration


def test_format_duration_uses_human_units_for_long_waits():
    assert format_duration(42) == "42s"
    assert format_duration(2327) == "38m 47s"
    assert format_duration(86378) == "23h 59m"
    assert format_duration(176400) == "2d 1h"
