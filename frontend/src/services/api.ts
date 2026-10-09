import type {
  HealthResponse,
  ReportCreate,
  SearchResponse,
} from '../types';

export interface SearchOptions {
  platform?: string;
  sort?: string;
  hasLocation?: boolean;
  language?: string;
  minViewers?: number;
}

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`, { signal });
  if (!res.ok) throw new Error(`health failed: ${res.status}`);
  return res.json() as Promise<HealthResponse>;
}

async function readError(res: Response, fallback: string): Promise<string> {
  // Surface the server's own `{"error": {"message"}}` (429, 422, 502 ...)
  // so users see "too many requests", not "search failed: 429".
  try {
    const body = (await res.json()) as { error?: { message?: string } };
    return body.error?.message || fallback;
  } catch {
    return fallback;
  }
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
  if (opts.language) {
    params.set('language', opts.language);
  }
  if (opts.minViewers) {
    params.set('min_viewers', String(opts.minViewers));
  }
  const res = await fetch(`${API_BASE}/api/search?${params.toString()}`, {
    signal,
  });
  if (!res.ok) {
    throw new Error(await readError(res, `search failed: ${res.status}`));
  }
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
