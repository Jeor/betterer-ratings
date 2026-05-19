from __future__ import annotations

import json
import logging
import sys

from betterer_ratings.config.schema import AppConfig
from betterer_ratings.observability.logging_setup import JsonLogFormatter, configure_logging


def test_logging_uses_stdout_json_handler_only(base_valid_config):
    config = AppConfig.from_mapping(base_valid_config)

    configure_logging(config)

    root = logging.getLogger()
    assert len(root.handlers) == 1
    handler = root.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream is sys.stdout
    assert handler.formatter is not None
    assert "FileHandler" not in type(handler).__name__


def test_json_formatter_adds_dozzle_friendly_context_fields():
    record = logging.LogRecord(
        name="betterer-ratings",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="[Submitter] Queue status: ratings(pending=1 in_flight=0 failed=0).",
        args=(),
        exc_info=None,
    )
    record.event = "queue.status"
    record.ratings_pending = 1

    payload = json.loads(JsonLogFormatter().format(record))

    assert "ts" not in payload
    assert payload["component"] == "submitter"
    assert payload["event"] == "queue.status"
    assert payload["ratings_pending"] == 1
