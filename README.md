# betterer-ratings

Autonomous Docker-first worker for harvesting TMDB and IMDb title data, enriching it with MDBList ratings, and submitting ratings and mappings to PMDB.

## Runtime Model

The service has one mode: start, run forever, and stop gracefully on SIGTERM/SIGINT. At startup it validates config, opens the SQLite database, recovers expired in-flight queue rows, and runs the harvester and submitter until the container stops.

The harvester loop always runs the same cycle:

- process IMDb episode ratings first
- skip title enrichment only while MDBList quota is paused
- refresh failed local titles, then TTL-stale titles, then new local rows
- run TMDB source scans on `worker.source_scan_interval_hours`
- ingest IMDb archive title candidates as part of source scans
- enrich candidates through MDBList and queue PMDB work

Logs are JSON lines on stdout. Docker or your host logging stack owns collection and rotation.

## Docker

```bash
cp config.example.toml config.toml
# edit config.toml with API keys
docker compose up -d --build
```

The compose file mounts:

- `./config.toml` at `/config/config.toml`
- `./data/db` at `/data/db`
- `./data/imdb` at `/data/imdb`
- `./data/temp` at `/data/temp`

The main database path inside the container is `/data/db/betterer_ratings.sqlite3`.

## Local Development

```bash
python3 -m pip install -e ".[dev]"
betterer-ratings --config config.toml
```

The CLI intentionally has no subcommands. It is the same worker entry point used by Docker.

## Config

Public config is limited to API keys, log level, scan and refresh intervals, TMDB source lists, IMDb filters, provider rate limits, and MDBList batch size. Runtime internals such as database paths, IMDb archive path, submitter worker count, retry counts, and provider timeouts are hardcoded for the container.

Defaults:

- title/movie/series ratings TTL: 7 days
- episode ratings TTL: 1 day
- IMDb archive refresh: daily at 13:00 UTC, using `https://datasets.imdbws.com`
- MDBList batch size: 100
- submitter workers: 16

Use `config.example.toml` as the schema reference.
