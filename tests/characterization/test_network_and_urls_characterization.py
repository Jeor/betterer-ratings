import socket

import httpx

from tests import support as m


def test_sanitize_url_for_logs_masks_sensitive_query_parameters():
    url = "https://example.test/path?api_key=abc&Token=xyz&q=hello+world&keep=1"
    assert (
        m.sanitize_url_for_logs(url)
        == "https://example.test/path?api_key=%2A%2A%2A&Token=%2A%2A%2A&q=hello+world&keep=1"
    )


def test_sanitize_url_for_logs_returns_original_when_no_query():
    url = "https://example.test/path"
    assert m.sanitize_url_for_logs(url) == url


def test_sanitize_url_for_logs_returns_input_on_parse_error():
    assert m.sanitize_url_for_logs(None) is None


def test_is_network_unavailable_error_true_for_timeout_and_connection_error():
    assert m.is_network_unavailable_error(httpx.TimeoutException("timeout")) is True
    assert m.is_network_unavailable_error(httpx.ConnectError("conn")) is True


def test_is_network_unavailable_error_true_for_marker_text_and_causes():
    assert (
        m.is_network_unavailable_error(
            RuntimeError("temporary failure in name resolution")
        )
        is True
    )

    with_cause = RuntimeError("generic")
    with_cause.__cause__ = socket.gaierror(8, "nodename nor servname provided")
    assert m.is_network_unavailable_error(with_cause) is True


def test_is_network_unavailable_error_false_for_non_network_request_exception():
    assert m.is_network_unavailable_error(RuntimeError("boom")) is False
