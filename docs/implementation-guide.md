# Live Event Search Engine — Implementation Guide

This guide is intentionally lighter than the sprint roadmap. It describes the implementation sequence and conventions; the roadmap contains the detailed verification-driven work.

## 1. Development Order

Implement one vertical slice at a time:

1. Repository and development environment.
2. FastAPI health endpoint.
3. React/Vite shell.
4. Search UI.
5. YouTube adapter.
6. Normalized stream model.
7. Search result API.
8. Result cards.
9. Playback/link handling.
10. Freshness verification.
11. Reporting.
12. Caching and quota protection.
13. Tests and deployment.
14. Twitch adapter after the YouTube vertical slice is proven.

Do not implement multiple platforms simultaneously during the MVP.

## 2. Configuration

Use environment variables:

```text
YOUTUBE_API_KEY=
DATABASE_URL=
APP_ENV=development
```

Never commit secrets.

## 3. Backend Conventions

Keep platform-specific logic inside:

```text
backend/app/adapters/
```

The adapter should:
- receive a normalized search request;
- call the platform;
- map the response to the common stream model;
- return platform-specific errors in a controlled form.

Search/business logic should not know YouTube response shapes.

## 4. Frontend Conventions

The frontend should consume normalized API responses rather than platform-specific response formats.

Components should remain small:

```text
SearchBar
SearchFilters
ResultsGrid
StreamCard
PlatformBadge
LiveStatus
SourceButton
ReportButton
```

Keep playback isolated from discovery.

## 5. MVP Search

Start with:

```text
GET /api/search?q=wildfire
```

Return:

```json
{
  "query": "wildfire",
  "results": [],
  "count": 0
}
```

Add structured filters only after basic search works.

## 6. Relevance

Start deterministic.

Example conceptual weighting:

```text
title exact match       high
title token match       high
description match       medium
category/tag match      medium
location match          high
freshness               medium
viewer count            low
```

Weights should be configurable rather than buried throughout the code.

## 7. Testing

Each sprint should have a concrete verification target.

At minimum:

- adapter unit tests
- search service tests
- API tests
- frontend component tests where worthwhile
- live integration smoke test
- failure handling tests
- stale-stream tests

Mock platform responses for most automated tests.

Use real API calls only for controlled integration testing.

## 8. Failure Handling

A platform can:
- timeout
- return quota errors
- return no results
- change metadata
- report a stream as live after it ends
- temporarily become unavailable

One platform failure must not take down the entire search response.

The API should be able to return partial results and platform status.

## 9. UI Philosophy

Keep the first UI clean rather than flashy.

Primary screen:

```text
------------------------------------------------
 What are you looking for happening live?
 [ wildfire near Los Angeles             🔎 ]
------------------------------------------------

 Filters: All | Nearby | Newest | Most Relevant

 🔴 LIVE
 ------------------------------------------------
 | thumbnail | stream title                   |
 |           | source / creator               |
 |           | location / time / viewers      |
 |           | [Watch] [Open Source]          |
 ------------------------------------------------
```

The search experience should remain the focus.

## 10. Deployment

Deploy frontend and backend independently if that simplifies hosting.

Before deployment verify:
- HTTPS
- API secret protection
- CORS configuration
- rate limits
- platform quota usage
- cache behavior
- source links
- embed policies

## 11. Expansion Rules

Do not add a new platform until:
- the existing adapter is stable;
- normalized records work correctly;
- search relevance is measurable;
- stale results are handled;
- API failure isolation works.

Then implement the next adapter against the same interface.

## 12. AI Expansion Gate

Do not add embeddings/LLMs merely because they are available.

First collect examples where deterministic search fails:

```text
query
expected relevant streams
actual returned streams
reason for mismatch
```

If a recurring class of failures exists, introduce semantic retrieval specifically to solve it.

## 13. Definition of MVP

MVP is complete when a user can:

1. Open the website.
2. Enter a real-world topic/event.
3. Search active YouTube broadcasts.
4. Receive normalized relevant results.
5. See which results are currently live/fresh.
6. Understand the source and creator.
7. Watch via an allowed embed or open the source.
8. Report a stale/broken/misclassified result.
9. Repeat searches without excessive API consumption.
