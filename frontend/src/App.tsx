import { useEffect, useState } from 'react';
import { fetchHealth } from './services/api';

type HealthState =
  | { status: 'loading' }
  | { status: 'ok'; env: string }
  | { status: 'error'; message: string };

export default function App() {
  const [health, setHealth] = useState<HealthState>({ status: 'loading' });

  useEffect(() => {
    const ctrl = new AbortController();
    fetchHealth(ctrl.signal)
      .then((h) => setHealth({ status: 'ok', env: h.env }))
      .catch((e: unknown) =>
        setHealth({
          status: 'error',
          message: e instanceof Error ? e.message : 'unknown error',
        }),
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
    </main>
  );
}
