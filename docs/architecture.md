# Live Event Search Engine — Architecture

## 1. Project Definition

A web application for discovering currently active public livestreams by **event, topic, situation, or location**, across multiple streaming platforms.

The product is event-first rather than creator-first:

> "Find live video about what is happening right now."

Example searches:
- wildfire near Los Angeles
- earthquake
- hurricane in Florida
- rocket launch
- concert in Tokyo
- protest downtown
- police chase
- breaking news

The system is an indexing/discovery layer. It should use official APIs, permitted feeds, embeds, and links where practical rather than downloading or redistributing source video.

## 2. Core Principles

1. Event-first, not creator-first.
2. Live-first.
3. Cross-platform.
4. Search before browsing.
5. Source transparency.
6. Do not host video unnecessarily.
7. Do not copy/re-distribute when linking or embedding is sufficient.
8. Platform adapters are replaceable.
9. Metadata first, AI second.
10. Location-aware when available.
11. Freshness is a first-class property.
12. Deduplicate the same broadcast/event where practical.
13. Separate discovery from playback.
14. Provide lightweight reporting/correction.
15. Build an index, not another social network.
16. Optimize for relevance, not raw aggregation volume.

## 3. MVP Scope

### Initial platform
- YouTube Live.

### Initial capabilities
- Search active broadcasts.
- Normalize results into a common stream model.
- Show title, creator, thumbnail, source platform, start time, viewer count when available, location when available, and source URL.
- Display freshness/live verification information.
- Open or embed supported source playback.
- Basic keyword/relevance matching.
- Responsive desktop/mobile web UI.
- Broken-link / no-longer-live reporting.

### Explicitly deferred
- TikTok integration.
- X integration.
- Video downloading/rehosting.
- Full computer-vision analysis.
- Complex social features.
- Large-scale event clustering.
- User accounts unless later justified.
- Native mobile application.

## 4. Platform Roadmap

The platform layer uses adapters so each source is isolated.

Initial:
- YouTube

Next:
- Twitch

Potential:
- Kick

Future experiments:
- TikTok
- X
- other public livestream platforms

The application must not assume that every platform supports the same search, playback, metadata, or geographic capabilities.

## 5. High-Level Architecture

```text
Browser
  |
  v
Search UI
  |
  v
Query / Search API
  |
  +--> Query Parser
  |
  +--> Platform Adapters
  |      +--> YouTube
  |      +--> Twitch
  |      +--> Kick
  |      +--> Future adapters
  |
  v
Normalized Stream Records
  |
  +--> Relevance
  +--> Freshness
  +--> Location
  +--> Deduplication
  |
  v
Ranked Results
  |
  +--> Embedded playback where permitted
  +--> External source links
```

## 6. Recommended Technology

### Frontend
- React
- Vite
- TypeScript
- CSS or a lightweight component approach
- Responsive grid/list UI

### Backend
- Python
- FastAPI

FastAPI is preferred because the project is fundamentally an API/search service and Python leaves room for later NLP/embedding work.

### Storage
Start with SQLite for the PoC.

Potential later migration:
- PostgreSQL

### Search
MVP:
- PostgreSQL/SQLite fields + deterministic relevance scoring.

Later:
- SQLite FTS5 or PostgreSQL full-text search.
- Embeddings/vector search when semantic search is justified.

### Caching
- In-memory cache initially.
- Redis only if traffic and polling requirements justify it.

### Deployment
PoC:
- Any low-cost/simple Python web host for backend.
- Static frontend hosting where practical.

The exact provider should be selected during implementation based on current free-tier/API constraints rather than hard-coded into the architecture.

## 7. Normalized Stream Model

Conceptual fields:

```text
Stream
├── id
├── platform
├── platform_stream_id
├── channel_id
├── channel_name
├── title
├── description
├── thumbnail_url
├── source_url
├── embed_url
├── embed_supported
├── live_status
├── started_at
├── discovered_at
├── last_verified_at
├── viewer_count
├── category
├── tags
├── latitude
├── longitude
├── location_text
└── metadata
```

Platform-specific data should remain available without forcing every platform into identical fields.

## 8. Search Model

A query may eventually be parsed into:

```text
SearchIntent
├── raw_query
├── topics
├── location
├── time_constraint
├── event_type
└── semantic_terms
```

MVP can initially treat the raw query as keywords and progressively introduce structured parsing.

## 9. Relevance Model

Initial deterministic scoring can consider:

- title match
- description match
- category/tag match
- location match
- exact phrase match
- freshness
- live verification
- viewer count as a secondary signal

Avoid using viewer count as the primary ranking signal because popularity and relevance are different concepts.

Later signals:
- semantic similarity
- captions/transcript relevance
- event clustering
- source reliability/freshness
- duplicate detection

## 10. Freshness Model

Important timestamps:

```text
discovered_at
last_verified_at
started_at
ended_at
```

A stream should not remain indefinitely marked LIVE because an earlier API response said it was live.

The index should periodically revalidate active records.

## 11. API Shape

Initial backend endpoints:

```text
GET /api/search?q={query}
GET /api/streams/{id}
GET /api/health
POST /api/reports
```

Possible future endpoints:

```text
GET /api/events/{id}
GET /api/events/{id}/streams
GET /api/search?location=...
GET /api/platforms
GET /api/trending
```

## 12. Suggested Repository Structure

```text
live-event-search/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── adapters/
│   │   │   ├── base.py
│   │   │   └── youtube.py
│   │   ├── models/
│   │   ├── search/
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── docs/
│   ├── architecture.md
│   ├── implementation-guide.md
│   └── sprint-roadmap.md
│
├── .env.example
├── README.md
└── .gitignore
```

## 13. Security and Operational Boundaries

- Never expose private API credentials in frontend source.
- Validate and sanitize user search input.
- Rate-limit backend endpoints where appropriate.
- Cache platform results to reduce unnecessary API usage.
- Do not proxy arbitrary URLs.
- Treat platform metadata as untrusted input.
- Do not store source video.
- Store only the metadata necessary for discovery.
- Respect platform API terms, robots/technical restrictions, copyright rules, and embed policies.
- Build adapters around documented/legitimate access wherever possible.

## 14. Quota Strategy

YouTube search requests have meaningful quota costs, so the architecture should avoid making an expensive platform search for every keystroke.

Use:
- Search on submit/debounced query.
- Result caching.
- Query normalization.
- Short-lived server cache.
- Platform-specific request budgets.
- Future index-based search when scale requires it.

Do not assume a browser-direct API architecture is the final production design.

## 15. Future Architecture

The long-term system may become:

```text
                   Search Query
                       |
                Query Understanding
                       |
                Event/Topic Search
                       |
             +---------+---------+
             |                   |
       Live Index            Event Index
             |                   |
       Platform Data       Event Correlation
             |                   |
             +---------+---------+
                       |
                  Relevance Engine
                       |
                Dedup / Clustering
                       |
                  Search Results
```

AI/semantic capabilities should be introduced only when deterministic search demonstrates a measurable limitation.

## 16. Architecture Decision Summary

- Build a web dashboard.
- Start with YouTube.
- Use a backend API rather than committing to browser-direct production architecture.
- Keep platform integrations behind adapters.
- Start with metadata-based relevance.
- Use SQLite for the initial index.
- Treat live verification and freshness as core data.
- Preserve source attribution.
- Prefer official embeds/links over video hosting.
- Design for Twitch/Kick additions without implementing them prematurely.
- Leave TikTok as a future technical experiment.
