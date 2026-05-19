FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

RUN mkdir -p /config /data/db /data/imdb /data/temp

CMD ["betterer-ratings", "--config", "/config/config.toml"]
