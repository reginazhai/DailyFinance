# DailyFinance

DailyFinance is an AI-powered financial intelligence platform that collects, normalizes, stores, and exposes financial information from multiple sources.

The project is designed around a modular data pipeline that separates data collection, processing, storage, and future AI analysis. By keeping raw data immutable and enriching it through deterministic processing before introducing LLMs, DailyFinance aims to provide reliable, explainable financial intelligence rather than simply aggregating news.

## Architecture

```text
             RSS feeds
        Website feed discovery
             yfinance
                |
                v
            Collectors
                |
                v
           RawDocument
                |
                v
       Ingestion Pipeline
                |
                v
        JSONL / SQLite
                |
                v
     Processing Pipeline
                |
                v
       ProcessedDocument
                |
                v
          FastAPI API
                |
                v
        Future LLM Layer
```

## Current Features

- RSS feed ingestion
- RSS feed discovery from website URLs
- Yahoo Finance market data collection through `yfinance`
- Immutable `RawDocument` model
- Deterministic `ProcessedDocument` metadata pipeline
- JSONL and SQLite storage
- JSONL-to-SQLite migration
- Duplicate prevention with stable document IDs
- URL and timestamp normalization
- Conservative ticker extraction
- Small ticker-to-company mapping
- Read-only FastAPI API
- Configurable RSS sources
- Offline unit tests

## Design Principles

- Raw data is immutable.
- Processing is deterministic.
- AI should augment structured data, not replace it.
- Every document retains source attribution.
- External services are wrapped behind collector interfaces.
- Components are modular and independently testable.

## Roadmap

### Completed

- [x] Python project foundation
- [x] Collector interface
- [x] RSS collection
- [x] RSS feed discovery
- [x] yfinance collection
- [x] JSONL storage
- [x] SQLite storage
- [x] FastAPI read-only API
- [x] Deterministic processing pipeline
- [x] Processed document persistence

### In Progress

- [ ] Broader deterministic metadata extraction
- [ ] Ticker normalization
- [ ] Company extraction from curated mappings
- [ ] Processed-document search filters

### Planned

- [ ] SEC EDGAR collection
- [ ] FRED/macroeconomic data collection
- [ ] Search and retrieval
- [ ] LLM-generated summaries
- [ ] Daily intelligence reports
- [ ] Portfolio monitoring
- [ ] Web dashboard

## Release Milestones

```text
v0.1  Collection + raw storage
v0.2  Deterministic metadata processing
v0.3  Search and retrieval
v0.4  LLM summaries
v0.5  Daily intelligence reports
v1.0  AI financial intelligence platform
```

Current project state: between `v0.2` and `v0.3`. Collection, storage, read-only APIs, and deterministic processing are implemented. LLM summarization is planned but not implemented yet.

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for local development
- JSONL for lightweight raw storage
- pytest
- feedparser
- yfinance

## Setup

Install the project in editable mode:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
```

## Ingestion Examples

Ingest one RSS feed directly:

```bash
dailyfinance-ingest \
  --source-name marketwatch_top_stories \
  --feed-url https://feeds.content.dowjones.io/public/rss/mw_topstories \
  --output-path data/raw_documents.jsonl
```

Discover RSS or Atom feeds from a website URL, then ingest the discovered feeds:

```bash
dailyfinance-ingest \
  --source-name example_site \
  --website-url https://example.com \
  --output-path data/raw_documents.jsonl
```

Ingest all configured RSS sources from `config/rss_sources.yaml`:

```bash
dailyfinance-ingest \
  --all-configured-rss \
  --output-path data/raw_documents.jsonl
```

Ingest recent market data with yfinance:

```bash
dailyfinance-ingest \
  --ticker AAPL \
  --ticker MSFT \
  --market-period 5d \
  --market-interval 1d \
  --output-path data/raw_documents.jsonl
```

## SQLite Workflow

Migrate existing JSONL documents into SQLite:

```bash
dailyfinance-migrate-jsonl-to-sqlite \
  --input-path data/raw_documents.jsonl \
  --database-url sqlite:///data/dailyfinance.db
```

Process raw SQLite documents into deterministic metadata records:

```bash
dailyfinance-process-sqlite \
  --database-url sqlite:///data/dailyfinance.db \
  --limit 100
```

By default, processing uses a recent daily window of 7 days so old backfill data does not crowd the daily workflow. To process historical records explicitly:

```bash
dailyfinance-process-sqlite \
  --database-url sqlite:///data/dailyfinance.db \
  --include-historical
```

## Local API

Run the read-only API against the default JSONL document store at `data/raw_documents.jsonl`:

```bash
python -m uvicorn dailyfinance.api.app:app --reload
```

Run the API against SQLite:

```bash
DAILYFINANCE_STORAGE_BACKEND=sqlite \
DAILYFINANCE_DATABASE_URL=sqlite:///data/dailyfinance.db \
python -m uvicorn dailyfinance.api.app:app --reload
```

Use a different JSONL document store path:

```bash
DAILYFINANCE_DOCUMENT_STORE_PATH=/tmp/dailyfinance_documents.jsonl \
python -m uvicorn dailyfinance.api.app:app --reload
```

Available read-only endpoints:

```text
GET /health
GET /documents?limit=20
GET /documents?source_name=marketwatch_top_stories
GET /documents/sources
GET /documents/{document_id}
GET /processed-documents?limit=20
GET /processed-documents?ticker=AAPL
GET /processed-documents?document_type=news
GET /processed-documents?recent_only=false
GET /processed-documents?recent_days=30
GET /processed-documents/{document_id}
```

Interactive API docs are available when the server is running:

```text
http://127.0.0.1:8000/docs
```

## Current Limitations

- No LLM summarization yet.
- No embeddings or vector search yet.
- No SEC EDGAR or FRED collector yet.
- No scheduled ingestion jobs yet.
- No authentication yet.
- No frontend dashboard yet.
- No PostgreSQL migration tooling yet.

## Recency Policy

DailyFinance keeps historical records in storage, but daily-facing processed-document workflows default to recent records.

- Default recent window: 7 days
- Override with `DAILYFINANCE_RECENT_DAYS`
- API override: `recent_days`
- API historical mode: `recent_only=false`
- Processing historical mode: `--include-historical`

This keeps the product aligned with daily financial intelligence while still allowing explicit historical backfills and analysis.
