from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional, Sequence

from betterer_ratings.app import run_app
from betterer_ratings.config.loader import load_config
from betterer_ratings.observability.logging_setup import configure_logging

LOGGER = logging.getLogger("betterer-ratings")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="betterer-ratings worker")
    parser.add_argument(
        "--config",
        default="/config/config.toml",
        help="Path to TOML config file (default: /config/config.toml)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    config_path = Path(args.config).expanduser().resolve()

    try:
        config = load_config(config_path)
        configure_logging(config)
        asyncio.run(run_app(config))
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by signal.")
        return 0
    except Exception:
        if logging.getLogger().handlers:
            LOGGER.exception("Fatal runtime error")
        else:
            print(f"[FATAL] Could not start betterer-ratings with {config_path}")
        return 1
    return 0
