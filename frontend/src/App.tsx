import { useEffect, useState } from 'react';
import ResultsList from './components/ResultsList';
import SearchBar from './components/SearchBar';
import SearchFilters from './components/SearchFilters';
import { DEFAULT_FILTERS, type FilterState } from './lib/filters';
import { fetchHealth, searchStreams } from './services/api';
import type { Stream } from './types';

type HealthState =
  | { status: 'loading' }
  | { status: 'ok'; env: string }
  | { status: 'error'; message: string };

type SearchState =
  | { status: 'idle' }
  | { status: 'empty-query' }
  | { status: 'loading'; query: string }
  | { status: 'ok'; query: string; streams: Stream[] }
  | { status: 'error'; query: string; message: string };

function errMessage(e: unknown): string {
  return e instanceof Error ? e.message : 'unknown error';
}

export default function App() {
  const [health, setHealth] = useState<HealthState>({ status: 'loading' });
  const [search, setSearch] = useState<SearchState>({ status: 'idle' });
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [submitted, setSubmitted] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchHealth(ctrl.signal)
      .then((h) => setHealth({ status: 'ok', env: h.env }))
      .catch((e: unknown) =>
        setHealth({ status: 'error', message: errMessage(e) }),
      );
    return () => ctrl.abort();
  }, []);

  // Submit search (debounced/submit only — never per-keystroke fan-out).
  // Filter changes re-run the active query server-side (cache-guarded).
  const execute = (query: string, opts: FilterState) => {
    setSearch({ status: 'loading', query });
    searchStreams(query, opts)
      .then((r) =>
        setSearch({ status: 'ok', query, streams: r.results }),
      )
      .catch((e: unknown) =>
        setSearch({ status: 'error', query, message: errMessage(e) }),
      );
  };

  const runSearch = (raw: string) => {
    const query = raw.trim();
    if (!query) {
      setSearch({ status: 'empty-query' });
      return;
    }
    setSubmitted(query);
    execute(query, filters);
  };

  const changeFilters = (next: FilterState) => {
    setFilters(next);
    if (submitted) execute(submitted, next);
  };

  // "Where available" for both dimensions: only values actually present in
  // the current results become options, so absent data never appears as a
  // fake filter choice.
  const platforms =
    search.status === 'ok'
      ? [...new Set(search.streams.map((s) => s.platform))]
      : [];
  const languages =
    search.status === 'ok'
      ? [
          ...new Set(
            search.streams
              .map((s) => s.language)
              .filter((l): l is string => Boolean(l)),
          ),
        ].sort()
      : [];

  return (
    <main style={{ maxWidth: 640, margin: '0 auto', padding: 24 }}>
      <h1>StreamSearch</h1>
      <p>What are you looking for happening live?</p>
      <SearchBar
        isLoading={search.status === 'loading'}
        onSearch={runSearch}
      />
      <SearchFilters
        platforms={platforms}
        languages={languages}
        value={filters}
        disabled={search.status === 'loading'}
        onChange={changeFilters}
      />

      <section aria-label="search results" aria-live="polite">
        {search.status === 'idle' && (
          <p data-testid="search-prompt">
            Enter a topic above to search live streams.
          </p>
        )}
        {search.status === 'empty-query' && (
          <p data-testid="search-hint">Type a topic above to search.</p>
        )}
        {search.status === 'loading' && (
          <p data-testid="search-loading">Searching for “{search.query}”…</p>
        )}
        {search.status === 'ok' && search.streams.length > 0 && (
          <>
            <p data-testid="search-count">
              Found {search.streams.length} live stream
              {search.streams.length === 1 ? '' : 's'} for “{search.query}”.
            </p>
            <ResultsList streams={search.streams} />
          </>
        )}
        {search.status === 'ok' && search.streams.length === 0 && (
          <p data-testid="search-empty">
            No live streams found for “{search.query}”.
          </p>
        )}
        {search.status === 'error' && (
          <p data-testid="search-error">
            Search failed for “{search.query}”: {search.message}
          </p>
        )}
      </section>

      {health.status === 'ok' && (
        <p data-testid="backend-health">Backend: ok ({health.env})</p>
      )}
      {health.status === 'error' && (
        <p data-testid="backend-error">Backend unreachable: {health.message}</p>
      )}
    </main>
  );
}
