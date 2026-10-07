import type {
  HealthResponse,
  ReportCreate,
  SearchResponse,
} from '../types';

export interface SearchOptions {
  platform?: string;
  sort?: string;
  hasLocation?: boolean;
}

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`, { signal });
  if (!res.ok) throw new Error(`health failed: ${res.status}`);
  return res.json() as Promise<HealthResponse>;
}

export async function searchStreams(
  query: string,
  opts: SearchOptions = {},
  signal?: AbortSignal,
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });
  if (opts.platform && opts.platform !== 'all') {
    params.set('platform', opts.platform);
  }
  if (opts.sort && opts.sort !== 'relevance') {
    params.set('sort', opts.sort);
  }
  if (opts.hasLocation) {
    params.set('has_location', 'true');
  }
  const res = await fetch(`${API_BASE}/api/search?${params.toString()}`, {
    signal,
  });
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
