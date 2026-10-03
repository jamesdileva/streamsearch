import { useEffect, useState } from 'react';
import { fetchHealth, searchStreams } from './services/api';
import type { Stream } from './types';

type HealthState =
  | { status: 'loading' }
  | { status: 'ok'; env: string }
  | { status: 'error'; message: string };

type PreviewState =
  | { status: 'loading' }
  | { status: 'ok'; stream: Stream | null }
  | { status: 'error'; message: string };

function errMessage(e: unknown): string {
  return e instanceof Error ? e.message : 'unknown error';
}

export default function App() {
  const [health, setHealth] = useState<HealthState>({ status: 'loading' });
  const [preview, setPreview] = useState<PreviewState>({ status: 'loading' });

  useEffect(() => {
    const ctrl = new AbortController();
    fetchHealth(ctrl.signal)
      .then((h) => setHealth({ status: 'ok', env: h.env }))
      .catch((e: unknown) =>
        setHealth({ status: 'error', message: errMessage(e) }),
      );
    return () => ctrl.abort();
  }, []);

  // Sprint 0.2 skeleton preview: proves a normalized adapter record
  // renders in the UI. Real search UI lands in Sprint 1.1.
  useEffect(() => {
    const ctrl = new AbortController();
    searchStreams('skeleton', ctrl.signal)
      .then((r) =>
        setPreview({ status: 'ok', stream: r.results[0] ?? null }),
      )
      .catch((e: unknown) =>
        setPreview({ status: 'error', message: errMessage(e) }),
      );
    return () => ctrl.abort();
  }, []);

  return (
    <main style={{ maxWidth: 640, margin: '0 auto', padding: 24 }}>
      <h1>StreamSearch</h1>
      <p>What are you looking for happening live?</p>
      {health.status === 'loading' && <p>Checking backend…</p>}
      {health.status === 'ok' && (
        <p data-testid="backend-health">Backend: ok ({health.env})</p>
      )}
      {health.status === 'error' && (
        <p data-testid="backend-error">Backend unreachable: {health.message}</p>
      )}

      <section aria-label="skeleton preview">
        <h2>Skeleton preview (fake adapter)</h2>
        {preview.status === 'loading' && <p>Loading preview…</p>}
        {preview.status === 'ok' && preview.stream && (
          <article data-testid="skeleton-stream">
            <p>
              [{preview.stream.live_status}] {preview.stream.title}
            </p>
            <p>
              {preview.stream.channel_name} · {preview.stream.platform}
            </p>
          </article>
        )}
        {preview.status === 'ok' && !preview.stream && (
          <p data-testid="skeleton-empty">No preview stream.</p>
        )}
        {preview.status === 'error' && (
          <p data-testid="skeleton-error">Preview failed: {preview.message}</p>
        )}
      </section>
    </main>
  );
}
