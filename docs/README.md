# betterer-ratings Notes

## Data Flow

`betterer-ratings --config /config/config.toml` runs two long-lived tasks:

- Harvester: discovers titles, refreshes stale ratings, processes IMDb archives, and queues PMDB writes.
- Submitter: claims the oldest due mapping, rating, or episode-rating work across all queues.

There are no discovery modes. Source scans, IMDb archive ingestion, IMDb episode rating ingestion, and local TTL refreshes are one continuous loop.

## IMDb Archives

IMDb datasets are stored in `/data/imdb` and refreshed daily at 13:00 UTC:

- `title.basics.tsv`
- `title.ratings.tsv`
- `title.episode.tsv`

Title ingestion uses IMDb archives to discover movie and series titles not found in TMDB list scans. Episode ingestion uses IMDb parent/episode/rating data and reprocesses after the episode TTL expires.

IMDb to TMDB resolution checks local mappings, local titles, and `imdb_tmdb_cache.sqlite3` before calling TMDB `/find`.

## Ratings

MDBList rating parsing emits PMDB labels including:

- `TM` for TMDB ratings
- `IM` for IMDb ratings
- `RT`, `MC`, and other existing labels
- `ML` for MyAnimeList/MAL
- `RE` for RogerEbert

Score normalization converts source scales to 0-100 values before queueing.

## Storage

Container paths are fixed:

- main database: `/data/db/betterer_ratings.sqlite3`
- IMDb archives/cache: `/data/imdb`
- temp indexes: `/data/temp`

The copied legacy database has been backed up into `data/db/betterer_ratings.sqlite3`; IMDb cache and TSV filenames remain provider-named.

## Logging

Logs are structured JSON on stdout only. File logging, Rich dashboards, event buffers, and dashboard status protocols were removed because Docker handles collection and retention.
