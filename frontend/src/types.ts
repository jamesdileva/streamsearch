export interface HealthResponse {
  status: string;
  env: string;
}

// Normalized stream (mirrors backend Stream model, Sprint 0.2 skeleton subset).
export interface Stream {
  id: string;
  platform: string;
  platform_stream_id: string;
  channel_id: string;
  channel_name: string;
  title: string;
  description: string;
  source_url: string;
  live_status: 'live' | 'ended' | 'unknown';
}

export interface SearchResponse {
  query: string;
  results: Stream[];
  count: number;
}
