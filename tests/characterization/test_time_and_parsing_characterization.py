import datetime as dt
import email.utils

import pytest

from tests import support as m


def test_local_day_key_with_explicit_timestamp_matches_python_timezone_conversion():
    ts = 1700000000
    expected = dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone().strftime("%Y-%m-%d")
    assert m.local_day_key(ts) == expected


def test_local_day_key_uses_now_epoch_when_ts_not_provided(monkeypatch):
    ts = 1700001234
    monkeypatch.setattr(m, "now_epoch", lambda: ts)
    expected = dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone().strftime("%Y-%m-%d")
    assert m.local_day_key() == expected


def test_to_iso_uses_expected_local_time_format():
    ts = 1700000000
    expected = (
        dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone().strftime("%d-%m-%y %H:%M:%S")
    )
    assert m.to_iso(ts) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        (" 42 ", 42),
        ("-7", -7),
        (" 001 ", 1),
        ("abc", None),
        ("12.3", None),
        ("", None),
        ("   ", None),
        (True, None),
        (3.0, None),
    ],
)
def test_parse_int_characterization(value, expected):
    assert m.parse_int(value) == expected


def test_parse_retry_after_defaults_when_missing_value():
    assert m.parse_retry_after(None, default_seconds=9) == 9
    assert m.parse_retry_after("", default_seconds=9) == 9


def test_parse_retry_after_integer_variants():
    assert m.parse_retry_after("12", default_seconds=5) == 12
    assert m.parse_retry_after("0", default_seconds=5) == 1
    assert m.parse_retry_after("-4", default_seconds=5) == 1


def test_parse_retry_after_http_date_in_future_uses_delta_seconds(freeze_utc_now):
    fixed = freeze_utc_now(1700000000)
    header_value = email.utils.format_datetime(fixed + dt.timedelta(seconds=120), usegmt=True)
    assert m.parse_retry_after(header_value, default_seconds=5) == 120


def test_parse_retry_after_http_date_in_past_is_minimum_one_second(freeze_utc_now):
    fixed = freeze_utc_now(1700000000)
    header_value = email.utils.format_datetime(fixed - dt.timedelta(seconds=30), usegmt=True)
    assert m.parse_retry_after(header_value, default_seconds=5) == 1


def test_parse_retry_after_invalid_value_falls_back_to_default():
    assert m.parse_retry_after("not-a-date", default_seconds=7) == 7


def test_chunks_splits_sequence_into_fixed_sized_slices():
    values = [1, 2, 3, 4, 5]
    assert list(m.chunks(values, 2)) == [[1, 2], [3, 4], [5]]


def test_chunks_with_zero_size_raises_value_error():
    with pytest.raises(ValueError):
        list(m.chunks([1], 0))
