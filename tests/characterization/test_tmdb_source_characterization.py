import pytest

from tests import support as m


def test_build_source_normalizes_movie_source_and_caps_max_pages():
    source = m.TMDBClient.build_source({"name": " /Movie/Popular ", "max_pages": 999})
    assert source.name == "movie/popular"
    assert source.endpoint == "/movie/popular"
    assert source.media_type_hint == "movie"
    assert source.max_pages == 500


def test_build_source_normalizes_tv_source_and_min_bounds_max_pages():
    source = m.TMDBClient.build_source({"name": "tv/top_rated", "max_pages": 0})
    assert source.name == "tv/top_rated"
    assert source.endpoint == "/tv/top_rated"
    assert source.media_type_hint == "tv"
    assert source.max_pages == 1


def test_build_source_trending_all_has_no_media_type_hint():
    source = m.TMDBClient.build_source({"name": "trending/all/day", "max_pages": 12})
    assert source.name == "trending/all/day"
    assert source.endpoint == "/trending/all/day"
    assert source.media_type_hint is None
    assert source.max_pages == 12


def test_build_source_rejects_unsupported_source_names_with_exact_message():
    with pytest.raises(ValueError, match=r"^Unsupported TMDB source name: invalid/source$"):
        m.TMDBClient.build_source({"name": "invalid/source"})
