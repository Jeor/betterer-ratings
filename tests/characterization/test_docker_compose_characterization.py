from __future__ import annotations

from pathlib import Path


def test_compose_uses_stable_container_name():
    compose_text = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "container_name: betterer-ratings" in compose_text
