# Live Event Search Engine — Sprint Roadmap

## Roadmap Philosophy

This roadmap is deliberately the most detailed document in the architecture suite.

The project should be built as a sequence of **verified vertical slices**, not as a large collection of unfinished infrastructure.

The guiding question throughout the roadmap is:

> **Can this system actually help someone find something happening live?**

Every sprint has:
- Goal
- Work
- Verification
- End state
- Explicit non-goals where useful

---

# Phase 0 — Foundation & Product Contract

## Sprint 0.1 — Repository Bootstrap

### Goal
Create a clean project foundation that can support the frontend, backend, documentation and future platform adapters.

### Work
- Create repository.
- Create `frontend/`.
- Create `backend/`.
- Create `docs/`.
- Add `.gitignore`.
- Add `.env.example`.
- Initialize React/Vite frontend.
- Initialize FastAPI backend.
- Add basic README.
- Establish development scripts.
- Establish formatting/linting conventions.
- Create placeholder adapter interface.

### Verification
- Frontend starts locally.
- Backend starts locally.
- Browser can reach frontend.
- Frontend can call backend.
- No secrets are committed.

### End Goal
A clean empty application with a working frontend/backend connection.

---

## Sprint 0.2 — Architecture Skeleton

### Goal
Make the core architectural boundaries real before feature work begins.

### Work
Implement:
- API routing layer.
- Configuration.
- Adapter base interface.
- Search service placeholder.
- Stream domain model.
- Basic error model.
- Health endpoint.
- Frontend service layer.

### Verification
- `/api/health` returns healthy.
- Frontend displays backend health.
- A fake adapter can return a normalized stream.
- The frontend can render that fake stream.

### End Goal
The application proves that platform-specific data can be transformed into a common stream representation.

---

# Phase 1 — First Vertical Slice

## Sprint 1.1 — Search Interface

### Goal
Build the actual primary user interaction.

### Work
Create:
- Search bar.
- Search button.
- Loading state.
- Empty state.
- Error state.
- Results container.
- Responsive layout.

Initial copy should make the product's purpose obvious:

> What are you looking for happening live?

### Verification
Test:
- empty query;
- normal query;
- long query;
- special characters;
- repeated searches;
- mobile-width layout.

### End Goal
The user can submit a search and receive a placeholder response.

---

## Sprint 1.2 — YouTube Adapter

### Goal
Connect the first real platform.

### Work
Implement the YouTube adapter using the currently supported official API.

Search for active broadcasts.

Map platform data into:

```text
platform
stream_id
channel
title
description
thumbnail
source_url
started_at
viewer_count
category
location
```

### Important
Do not put YouTube-specific response handling into the frontend.

### Verification
Search real queries such as:
- news
- wildfire
- storm
- gaming
- concert

Confirm returned streams are actually active broadcasts.

### End Goal
The application can discover real live YouTube streams.

---

## Sprint 1.3 — Real Search Results

### Goal
Replace placeholder data with real results end-to-end.

### Work
Connect:

```text
SearchBar
    ↓
Frontend API client
    ↓
FastAPI
    ↓
Search service
    ↓
YouTube adapter
    ↓
Normalized Stream
    ↓
Frontend cards
```

### Verification
For at least five unrelated queries:
- results appear;
- titles match source;
- thumbnails match source;
- links work;
- platform is identified;
- no raw YouTube API response leaks into the UI.

### End Goal
**First meaningful MVP milestone: a functional live-event search engine for YouTube.**

---

# Phase 2 — Make the Results Trustworthy

## Sprint 2.1 — Stream Cards

### Goal
Make results useful rather than simply technically correct.

### Work
Create polished but restrained cards containing:
- live indicator;
- title;
- creator/channel;
- platform;
- thumbnail;
- start time;
- viewer count where available;
- location where available;
- source button;
- watch button if supported.

### Verification
Compare cards against actual source pages.

### End Goal
A user can understand a result without opening it first.

---

## Sprint 2.2 — Live Freshness

### Goal
Prevent stale information from looking current.

### Work
Add:
- `discovered_at`;
- `last_verified_at`;
- live status;
- stale state.

Define freshness thresholds.

Example:

```text
Fresh
Recently verified

Aging
Verification becoming old

Stale
Should be rechecked

Ended
No longer live
```

### Verification
Simulate:
- fresh stream;
- stream ending;
- failed verification;
- delayed API response.

### End Goal
The application communicates how trustworthy its live status is.

---

## Sprint 2.3 — Broken/Stale Reporting

### Goal
Give users a simple way to report bad index data.

### Work
Add:
- Report Broken Link.
- No Longer Live.
- Wrong Topic.
- Other.

Store reports locally/server-side.

### Verification
Submit each report type and verify persistence.

### End Goal
Users can feed corrections back into the system.

---

# Phase 3 — Search Relevance

## Sprint 3.1 — Deterministic Relevance

### Goal
Stop treating every API result as equally useful.

### Work
Implement configurable scoring for:
- exact title match;
- title token match;
- description match;
- tags/category;
- location;
- freshness.

Keep the scoring function isolated.

### Verification
Create a small manually labeled test set:

```text
query
relevant
partially relevant
irrelevant
```

Confirm obvious matches rise above weak keyword matches.

### End Goal
The application begins behaving like a search engine rather than an API viewer.

---

## Sprint 3.2 — Search Normalization

### Goal
Make common natural-language queries work without an AI model.

### Work
Normalize:
- casing;
- punctuation;
- whitespace;
- common synonyms where deterministic mappings are reliable.

Examples:

```text
LA → Los Angeles
wildfires → wildfire
earthquakes → earthquake
```

Avoid creating a giant hand-written ontology.

### Verification
Run equivalent queries and compare result quality.

### End Goal
Small query variations produce sensible results.

---

## Sprint 3.3 — Location-Aware Search

### Goal
Use location when the source provides it.

### Work
Support queries conceptually such as:

```text
wildfire near Los Angeles
storm Florida
concert Tokyo
```

Parse simple location expressions.

Use platform geographic search where supported.

Store normalized location fields.

### Verification
Test:
- known location;
- unknown location;
- location with no matching streams;
- location plus topic.

### End Goal
Location becomes a useful search dimension rather than decorative metadata.

---

# Phase 4 — Indexing & Efficiency

## Sprint 4.1 — Search Result Caching

### Goal
Reduce repeated platform requests and protect API quotas.

### Work
Implement short-lived caching keyed by normalized search parameters.

Track:
- cache hit;
- cache miss;
- API request count;
- error count.

### Verification
Run the same search repeatedly and confirm the platform isn't queried unnecessarily.

### End Goal
Repeated searches are cheap and fast.

---

## Sprint 4.2 — Persistent Stream Index

### Goal
Move from purely request-time discovery toward an actual searchable live index.

### Work
Store normalized stream records.

Implement:
- upsert;
- last-seen timestamps;
- live status;
- cleanup of old records.

### Verification
- Same stream does not create unlimited duplicates.
- Updated metadata overwrites correctly.
- Ended streams transition correctly.
- Old records can be removed/archived.

### End Goal
The project has a real live-stream index.

---

## Sprint 4.3 — Background Refresh

### Goal
Keep active stream information fresh without waiting for users to search.

### Work
Add a background refresh mechanism.

Initial behavior can be modest:
- refresh known active streams;
- expire stale records;
- discover popular/common queries only if justified.

Do not build a huge crawler yet.

### Verification
Start with a controlled test set and observe:
- discovery;
- refresh;
- ending;
- expiration.

### End Goal
The index has continuous freshness rather than being purely request-driven.

---

# Phase 5 — Second Platform

## Sprint 5.1 — Platform Adapter Contract Review

### Goal
Prove the architecture really supports a second platform.

### Work
Review YouTube-specific assumptions.

Ensure the adapter interface supports:
- different IDs;
- missing thumbnails;
- different viewer metrics;
- different location availability;
- different category systems;
- different playback capabilities;
- different live-state behavior.

### Verification
Implement a fake second platform using fixture data.

### End Goal
The architecture is genuinely platform-agnostic.

---

## Sprint 5.2 — Twitch Discovery

### Goal
Add the second real platform.

### Work
Implement Twitch adapter using legitimate supported API access.

Normalize:
- channel;
- stream;
- category;
- title;
- viewers;
- start time;
- URL;
- thumbnail;
- live status.

### Verification
Search topics where both YouTube and Twitch have relevant results.

### End Goal
One query returns results from two independent live platforms.

---

## Sprint 5.3 — Unified Cross-Platform Results

### Goal
Stop thinking in platform columns.

### Work
Combine results into a unified ranking.

Add filters:
- platform;
- relevance;
- newest;
- viewer count;
- location where available.

### Verification
Confirm a query can produce a mixed result set without one platform automatically dominating.

### End Goal
**Second major milestone: a true cross-platform live-event search prototype.**

---

# Phase 6 — Event Thinking

## Sprint 6.1 — Event vs. Stream Data Model

### Goal
Introduce the concept that multiple streams can relate to one event.

### Work
Design:

```text
Event
├── event_id
├── topic
├── location
├── detected_at
├── active_until
└── related_streams[]
```

Do not automatically cluster everything yet.

### Verification
Create manual event groups containing multiple streams.

### End Goal
The data model can represent:

> One event → many broadcasts.

---

## Sprint 6.2 — Basic Duplicate Detection

### Goal
Reduce obvious duplicate streams.

### Work
Detect likely duplicates using:
- identical source/channel;
- identical platform IDs;
- highly similar titles;
- same creator;
- timing overlap.

### Verification
Use a manually created duplicate test set.

### End Goal
The search engine can recognize simple duplicates without accidentally collapsing unrelated streams.

---

## Sprint 6.3 — Event Clustering Experiment

### Goal
Test whether streams can be grouped around an ongoing event.

### Work
Experiment with:
- title similarity;
- location;
- timing;
- shared entities;
- semantic similarity if necessary.

Keep it experimental.

### Verification
Use several real-world event examples and inspect false-positive/false-negative clustering.

### End Goal
Determine whether event clustering provides enough value to justify further development.

---

# Phase 7 — Semantic Search Experiment

## Sprint 7.1 — Failure Dataset

### Goal
Determine whether keyword search is actually insufficient.

### Work
Collect queries where:
- relevant streams lack exact keywords;
- synonyms are missed;
- descriptions carry the important context;
- titles are vague.

Record:

```text
query
expected result
actual result
failure reason
```

### Verification
Build a small benchmark.

### End Goal
A measured answer to:

> Do we actually need semantic search?

---

## Sprint 7.2 — Embedding Search Prototype

### Goal
Experiment with semantic relevance without making it mandatory.

### Work
Create embeddings for stream metadata.

Compare:
- keyword score;
- semantic score;
- hybrid score.

### Verification
Run the benchmark from Sprint 7.1.

### End Goal
Determine whether semantic retrieval measurably improves event discovery.

---

## Sprint 7.3 — Hybrid Ranking

### Goal
If justified, combine deterministic and semantic relevance.

### Work
Potential ranking:

```text
keyword relevance
+
semantic relevance
+
location relevance
+
freshness
+
live verification
```

Viewer count remains secondary.

### Verification
Compare hybrid results to the deterministic baseline.

### End Goal
Only keep semantic ranking if the measured improvement is meaningful.

---

# Phase 8 — User Experience

## Sprint 8.1 — Search Filters

### Goal
Make large result sets manageable.

### Work
Filters:
- All platforms
- YouTube
- Twitch
- future platforms
- newest
- most relevant
- nearby
- language where available
- viewer count where available

### Verification
Filters work without changing the underlying search semantics incorrectly.

### End Goal
Users can quickly narrow live results.

---

## Sprint 8.2 — Map Experiment

### Goal
Determine whether geographic visualization adds meaningful value.

### Work
Prototype:
- map;
- stream markers;
- event clusters;
- location confidence.

### Verification
Use only streams with meaningful geographic data.

### End Goal
A decision on whether the map belongs in the main product.

---

## Sprint 8.3 — Mobile/Responsive Pass

### Goal
Make the product useful on phones without turning it into a separate mobile application.

### Work
- responsive search;
- compact cards;
- touch targets;
- source links;
- optional full-screen playback.

### Verification
Test common mobile widths and real-device browser behavior.

### End Goal
The web application is usable on desktop and mobile.

---

# Phase 9 — Platform Expansion

## Sprint 9.1 — Kick Feasibility

### Goal
Evaluate Kick based on current legitimate data-access options.

### Work
Research current API/access requirements.

Do not assume scraping is acceptable.

### Verification
Document:
- available discovery mechanism;
- live status;
- metadata;
- playback;
- rate limits;
- terms/constraints.

### End Goal
A go/no-go decision backed by current technical information.

---

## Sprint 9.2 — Kick Adapter

### Goal
If feasible, add Kick using the established adapter contract.

### Verification
Cross-platform searches with YouTube/Twitch/Kick.

### End Goal
Three-platform live event discovery.

---

# Phase 10 — Reliability & Production Hardening

## Sprint 10.1 — Platform Failure Isolation

### Goal
A broken platform should not break the search engine.

### Work
Support:
- timeout;
- quota exhaustion;
- authentication failure;
- malformed response;
- empty result;
- temporary outage.

### Verification
Simulate each failure while another adapter remains healthy.

### End Goal
Partial results remain usable.

---

## Sprint 10.2 — Rate Limiting & Abuse Protection

### Goal
Protect the service and platform API quotas.

### Work
- request limits;
- query length limits;
- cache policy;
- suspicious query protection;
- logging.

### Verification
Automated request burst tests.

### End Goal
The service behaves predictably under excessive requests.

---

## Sprint 10.3 — Observability

### Goal
Know whether the index is actually healthy.

### Work
Track:
- searches;
- cache hits;
- adapter latency;
- adapter failures;
- streams discovered;
- stale streams;
- report volume;
- API quota usage.

### Verification
Dashboard/log inspection.

### End Goal
Operational problems are visible rather than discovered through user complaints.

---

# Phase 11 — Content & Safety Boundaries

## Sprint 11.1 — Source and Content Handling Review

### Goal
Make the indexing boundary explicit.

### Work
Document:
- source attribution;
- embed behavior;
- external links;
- prohibited local storage;
- reporting;
- platform takedown/removal handling;
- treatment of disturbing thumbnails/content.

The system is an index/discovery layer, not an archive or broadcaster.

### Verification
Review representative results and ensure the UI accurately identifies the originating platform.

### End Goal
Clear product and technical boundaries.

---

## Sprint 11.2 — Search Abuse Controls

### Goal
Prevent the search interface from becoming a mechanism for abusive targeting.

### Work
Evaluate:
- spam queries;
- malicious metadata;
- doxxing-style searches;
- personal information exposure;
- platform-specific abuse.

Implement only controls justified by observed/product requirements.

### Verification
Test representative problematic inputs.

### End Goal
Search remains useful while avoiding unnecessary collection or amplification of sensitive information.

---

# Phase 12 — TikTok as a Separate Experiment

## Sprint 12.1 — TikTok Feasibility Research

### Goal
Treat TikTok as an experiment rather than a dependency.

### Work
Research current:
- official APIs;
- public discovery options;
- developer requirements;
- rate limits;
- terms;
- embed capabilities;
- live metadata accessibility.

### Verification
Produce a technical feasibility report.

### End Goal
A clear answer to:

> Can TikTok be integrated legitimately and sustainably?

---

## Sprint 12.2 — TikTok Adapter Prototype

### Goal
Only if Sprint 12.1 supports it, build an isolated prototype.

### Work
Implement a separate adapter without changing the core search architecture.

### Verification
Return normalized stream records.

### End Goal
Prove or disprove TikTok integration independently.

---

# Phase 13 — Advanced Live Intelligence

These sprints are intentionally optional.

## Sprint 13.1 — Caption/Transcript Relevance

Investigate whether captions/transcripts can improve topic detection.

Example:

```text
Title:
LIVE

Transcript:
"fire crews have just arrived..."
```

This could make vague streams discoverable.

### End Goal
Determine whether transcript indexing is practical and useful.

---

## Sprint 13.2 — Advanced Event Detection

Experiment with identifying:

```text
event
location
time
entities
related streams
```

from multiple broadcasts.

### End Goal
Move from stream search toward event search.

---

## Sprint 13.3 — Computer Vision Experiment

Only if justified.

Potential question:

> Can visual analysis identify relevant live streams whose metadata is poor?

Example:

```text
Search: wildfire

Stream title:
"Live from Highway 18"

Vision:
smoke/fire visible
```

This is expensive and should remain experimental.

### End Goal
Measure whether visual understanding produces enough discovery improvement to justify the cost.

---

# Phase 14 — Alerts & Saved Searches

## Sprint 14.1 — Saved Searches

### Goal
Allow users to monitor topics.

Example:

```text
Saved:
"wildfire near Los Angeles"
```

### End Goal
A user can return to a query without rebuilding it.

---

## Sprint 14.2 — Live Event Alerts

### Goal
Notify users when a matching live event appears.

Potential triggers:

```text
new relevant stream
major increase in matching streams
new event cluster
```

### End Goal
The system moves from passive search toward live monitoring.

---

# Phase 15 — Long-Term Product Experiments

These are not commitments.

Potential experiments:

- event timeline;
- geographic event map;
- multi-source event view;
- stream comparison;
- source reliability indicators;
- multilingual search;
- automatic topic expansion;
- breaking-event detection;
- natural-language questions;
- "what's happening near me?" search;
- historical event replay using metadata only;
- creator/source discovery as a secondary feature.

The core product should remain recognizable even if these experiments are never built.

---

# MVP Milestones

## Milestone A — YouTube Proof

The user can search:

```text
wildfire
```

and receive active, relevant YouTube broadcasts.

**Proves:** the fundamental interaction works.

## Milestone B — Trustworthy Search

Results have:
- relevance;
- freshness;
- source attribution;
- location where available;
- reporting.

**Proves:** the system is more than an API demo.

## Milestone C — Cross-Platform Search

YouTube + Twitch results appear in one relevance-ranked result set.

**Proves:** the adapter architecture works.

## Milestone D — Event Intelligence

Multiple streams can be connected to the same event.

**Proves:** the product is becoming event-first rather than merely cross-platform.

## Milestone E — Semantic Search

Measured testing demonstrates whether semantic retrieval improves discovery.

**Proves or disproves:** whether AI materially improves the core product.

---

# Suggested Priority Order

```text
FOUNDATION
   ↓
YOUTUBE
   ↓
REAL SEARCH
   ↓
FRESHNESS
   ↓
RELEVANCE
   ↓
LOCATION
   ↓
CACHE / INDEX
   ↓
TWITCH
   ↓
CROSS-PLATFORM
   ↓
EVENT MODEL
   ↓
SEMANTIC EXPERIMENT
   ↓
KICK
   ↓
OPTIONAL ADVANCED FEATURES
   ↓
TIKTOK EXPERIMENT
```

Do not reverse this order by building AI, maps, five platform adapters, or event clustering before proving the basic search loop.

---

# Verification Philosophy

Every major feature should answer one of four questions:

### Does it work?

Functional verification.

### Is it accurate?

Compare against source/platform truth.

### Is it useful?

Test actual searches.

### Does it scale reasonably?

Measure API requests, latency, cache behavior and failure handling.

A feature that works technically but makes search worse should not automatically survive.

---

# Final Definition of Done

The project has achieved its core objective when a person can enter something like:

> **"wildfire near Los Angeles"**

and the system can:

1. Understand the basic topic/location.
2. Search currently active supported livestreams.
3. Return relevant results.
4. Identify where each result came from.
5. Indicate how fresh/live the result is.
6. Provide location when available.
7. Avoid obvious irrelevant results.
8. Allow the user to watch or open the originating source.
9. Combine multiple platforms once those adapters exist.
10. Continue working when an individual platform is unavailable.

The project does **not** need AI, five platforms, a map, accounts, alerts, or computer vision to satisfy this definition.

That keeps the central experiment extremely clear:

> **Can we make the live internet searchable by what is happening right now?**
