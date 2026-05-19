from __future__ import annotations

import socket

import httpx


def is_network_unavailable_error(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError)):
        return True
    marker_text = str(exc).lower()
    markers = (
        "nameresolutionerror",
        "failed to resolve",
        "temporary failure in name resolution",
        "nodename nor servname provided",
        "network is unreachable",
        "no route to host",
        "connection refused",
    )
    if any(marker in marker_text for marker in markers):
        return True

    cause = getattr(exc, "__cause__", None)
    if isinstance(cause, (socket.gaierror, TimeoutError, OSError)):
        return True

    return False
