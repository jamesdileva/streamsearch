import type {
  HealthResponse,
  ReportCreate,
  SearchResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`, { signal });
  if (!res.ok) throw new Error(`health failed: ${res.status}`);
  return res.json() as Promise<HealthResponse>;
}

export async function searchStreams(
  query: string,
  signal?: AbortSignal,
): Promise<SearchResponse> {
  const res = await fetch(
    `${API_BASE}/api/search?q=${encodeURIComponent(query)}`,
    { signal },
  );
  if (!res.ok) throw new Error(`search failed: ${res.status}`);
  return res.json() as Promise<SearchResponse>;
}

export async function submitReport(report: ReportCreate): Promise<void> {
  const res = await fetch(`${API_BASE}/api/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(report),
  });
  if (!res.ok) throw new Error(`report failed: ${res.status}`);
}

export { API_BASE };
