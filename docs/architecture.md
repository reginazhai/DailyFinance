# Architecture

DailyFinance is organized into several layers:

## Data Collection

Collectors gather information from external sources such as:

- Financial news APIs
- SEC filings
- Earnings calendars
- Macroeconomic data sources
- Market data sources

## Processing

Raw information is cleaned, deduplicated, normalized, and enriched.

Processing may include:

- Text cleaning
- Source metadata extraction
- Company/entity extraction
- Keyword search indexing
- Sentiment or relevance scoring
- Chunking for retrieval

DailyFinance now distinguishes between immutable raw documents and deterministic
processed documents.

Raw documents preserve collected source data and raw payloads. Processed
documents are separately stored records derived from raw documents. The first
processing milestone performs deterministic enrichment only:

- whitespace normalization for titles and content
- source type and document type inference
- conservative ticker extraction from metadata, yfinance payloads, and explicit
  `$TICKER` text
- company mapping from a small configured ticker-to-company dictionary

Processed records retain a reference to the original raw document and a
processing version so the same raw document can be processed idempotently.

DailyFinance preserves historical records but treats daily-facing processed
document workflows as recent by default. The default recent window is seven
days and can be overridden for explicit backfills or historical analysis.

## Search And Retrieval

Processed documents are indexed with SQLite FTS5 for local keyword search.

The search index includes:

- normalized titles
- normalized content
- ticker symbols
- company names from curated ticker-to-company mappings

The index is synchronized when processed documents are saved and can be rebuilt
from SQLite with the search-index rebuild CLI. Search results return public
retrieval fields such as document IDs, snippets, tickers, companies, source
names, dates, and URLs. Raw payloads remain available through raw document
storage but are not returned in search responses by default.

This is intentionally keyword search only. Embeddings, semantic search, and
LLM-generated answers are future layers.

## Storage

The application stores structured and unstructured financial information.

Possible storage:

- SQLite for local development
- PostgreSQL for production
- Vector database for semantic search later

Current local storage supports:

- JSONL storage for raw documents
- SQLite storage for raw documents, sources, processed documents, and queryable
  processed-document ticker associations
- SQLite FTS5 index for processed-document keyword search

Database migrations are not yet introduced; SQLAlchemy creates local SQLite
tables for development.

## AI Layer

The AI layer summarizes and analyzes collected information.

Planned features:

- Daily market summaries
- Company-specific summaries
- Retrieval-augmented question answering
- Event extraction
- Personalized reports

## API Layer

FastAPI will expose endpoints for retrieving summaries, documents, companies, and reports.

## Project Structure

src/

    collectors/
        news/
        sec/
        macro/

    processing/
        cleaning/
        normalization/
        enrichment/

    storage/
        database/
        repositories/

    ai/
        summarization/
        retrieval/

    api/

    models/

    config/

    utils/
