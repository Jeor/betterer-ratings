import pytest

from tests import support as m


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, False),
        ("tt123", True),
        (" tt42 ", True),
        ("TT123", False),
        ("tt", False),
        ("abc", False),
    ],
)
def test_is_valid_imdb_title_id_characterization(value, expected):
    assert m.is_valid_imdb_title_id(value) is expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("tt123", "tt123"),
        (" tt123 ", "tt123"),
        ("TT123", None),
        ("", None),
    ],
)
def test_normalize_imdb_title_id_characterization(value, expected):
    assert m.normalize_imdb_title_id(value) == expected


@pytest.mark.parametrize(
    "title_type, expected",
    [
        ("movie", "movie"),
        ("tvMovie", "movie"),
        ("tvSeries", "tv"),
        ("tvMiniSeries", "tv"),
        ("documentary", None),
        (None, None),
    ],
)
def test_imdb_title_type_to_media_type_characterization(title_type, expected):
    assert m.imdb_title_type_to_media_type(title_type) == expected


@pytest.mark.parametrize(
    "values, expected",
    [
        ((None, "", "  ", "value"), "value"),
        ((" null ", "N/A", "  ok  "), "ok"),
        (("none", "NULL", None), None),
    ],
)
def test_first_non_empty_characterization(values, expected):
    assert m.first_non_empty(*values) == expected


def test_extract_mappings_uses_priority_order_and_normalizes_imdb():
    tmdb_details = {
        "external_ids": {
            "imdb_id": " tt12345 ",
            "tvdb_id": " 987 ",
        },
        "imdb_id": "tt99999",
    }
    mdblist_item = {
        "ids": {
            "imdb": "tt77777",
            "tvdb": "111",
            "trakt": "22",
            "mal": "33",
            "anilist": "44",
            "anidb": "55",
        },
        "imdbid": "tt88888",
    }

    assert m.extract_mappings("movie", tmdb_details, mdblist_item) == {
        "imdb": "tt12345",
        "tvdb": "987",
        "trakt": "22",
        "mal": "33",
        "anilist": "44",
        "anidb": "55",
    }


def test_extract_mappings_ignores_invalid_imdb_and_uses_fallback_candidates():
    tmdb_details = {
        "external_ids": {
            "imdb_id": "bad-id",
            "tvdb_id": "",
        },
        "imdb_id": "also-bad",
    }
    mdblist_item = {
        "ids": {
            "imdb": "tt54321",
            "tvdb": "12",
            "trakt": "null",
        },
    }

    assert m.extract_mappings("tv", tmdb_details, mdblist_item) == {
        "tvdb": "12",
    }


def test_extract_mappings_drops_empty_and_nullish_values():
    tmdb_details = {"external_ids": {"tvdb_id": "   "}}
    mdblist_item = {
        "ids": {
            "trakt": "",
            "mal": "none",
            "anidb": "N/A",
            "anilist": "123",
        }
    }

    assert m.extract_mappings("movie", tmdb_details, mdblist_item) == {
        "anilist": "123",
    }
