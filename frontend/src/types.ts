export interface HealthResponse {
  status: string;
  env: string;
}

// Normalized stream (mirrors backend Stream model; card-relevant subset).
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
  started_at: string | null;
  viewer_count: number | null;
  location_text: string | null;
}

export interface SearchResponse {
  query: string;
  results: Stream[];
  count: number;
}
