from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def sanitize_url_for_logs(url: str) -> str:
    sensitive_keys = {
        "api_key",
        "apikey",
        "token",
        "access_token",
        "auth",
        "authorization",
        "key",
    }
    try:
        parts = urlsplit(url)
        if not parts.query:
            return url
        sanitized_query = []
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            if key.lower() in sensitive_keys:
                sanitized_query.append((key, "***"))
            else:
                sanitized_query.append((key, value))
        return urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path,
                urlencode(sanitized_query, doseq=True),
                parts.fragment,
            )
        )
    except Exception:
        return url
