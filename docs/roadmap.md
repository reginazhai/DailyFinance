# Roadmap

## Phase 1: Project Foundation

- Set up Python project structure
- Add configuration management
- Add logging
- Add basic tests
- Create placeholder FastAPI app

## Phase 2: Data Collection

- Add first news collector
- Define common collector interface
- Store raw collected documents
- Add deduplication logic

## Phase 3: Processing Pipeline

- Normalize collected documents
- Extract metadata
- Add company/entity extraction
- Add basic summarization

Current progress:

- Added deterministic raw-to-processed document pipeline
- Added processed document model and SQLite persistence
- Added queryable ticker associations for processed documents
- Added conservative ticker extraction and small ticker-to-company mapping
- Added processed-document API endpoints
- Added recency policy so daily workflows default to recent records while
  historical records remain available explicitly

Remaining:

- Broaden deterministic metadata extraction
- Add more robust normalized entities
- Add basic search over processed documents
- Add basic summarization after deterministic enrichment is stable

## Phase 4: Storage

- Add database models
- Add migrations
- Store articles, sources, companies, and summaries

## Phase 5: AI Features

- Add LLM-based daily summary generation
- Add retrieval/search
- Add company-specific reports

## Phase 6: Frontend / Product Layer

- Add simple UI or dashboard
- Display daily finance briefings
- Support search and filtering

# Current Priority

Current objective:

Build a reliable pipeline that collects and stores financial information.

Current focus:

- Project setup
- Configuration
- First data collector
- Storage layer
- Deterministic metadata enrichment

Future AI features will only be added after the data pipeline is stable.

---

# Future Ideas

Potential future features:

- Earnings calendar
- SEC filing parser
- Company profiles
- Portfolio tracking
- Daily email reports
- Multi-agent analysis
- RAG over historical news
- Personalized recommendations
