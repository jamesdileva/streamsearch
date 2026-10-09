export interface HealthResponse {
  status: string;
  env: string;
}

// Normalized stream (mirrors backend Stream model; UI-relevant subset).
export type Freshness = 'fresh' | 'aging' | 'stale' | 'ended';

export interface Stream {
  id: string;
  platform: string;
  platform_stream_id: string;
  channel_id: string;
  channel_name: string;
  title: string;
  description: string;
  thumbnail_url: string;
  source_url: string;
  embed_url: string | null;
  embed_supported: boolean;
  live_status: 'live' | 'ended' | 'unknown';
  freshness: Freshness | null;
  started_at: string | null;
  last_verified_at: string | null;
  viewer_count: number | null;
  language: string | null;
  location_text: string | null;
  // Query-relative ranking score stamped by the backend (Sprint 3.1).
  // Displayed nowhere; result order is the feature.
  score: number | null;
}

export interface PlatformStatus {
  platform: string;
  status: 'ok' | 'error';
  detail?: string | null;
}

export interface SearchResponse {
  query: string;
  results: Stream[];
  count: number;
  duplicates_removed: number;
  platform_status: PlatformStatus[];
}

// Correction reports (mirrors backend report model).
export type ReportReason =
  | 'broken_link'
  | 'no_longer_live'
  | 'wrong_topic'
  | 'other';

export interface ReportCreate {
  stream_id: string;
  platform: string;
  reason: ReportReason;
  detail?: string;
}
