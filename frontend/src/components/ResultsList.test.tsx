import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import ResultsList from './ResultsList';
import type { Stream } from '../types';

const STREAMS: Stream[] = [
  {
    id: 'a',
    platform: 'fake',
    platform_stream_id: 'a',
    channel_id: 'c-a',
    channel_name: 'Channel A',
    title: 'Title A',
    description: '',
    thumbnail_url: '',
    source_url: 'https://example.com/a',
    embed_url: null,
    embed_supported: false,
    live_status: 'live',
    freshness: 'fresh',
    started_at: null,
    last_verified_at: null,
    score: null,
    viewer_count: null,
    location_text: null,
    language: 'en',
  },
  {
    id: 'b',
    platform: 'fake',
    platform_stream_id: 'b',
    channel_id: 'c-b',
    channel_name: 'Channel B',
    title: 'Title B',
    description: '',
    thumbnail_url: '',
    source_url: 'https://example.com/b',
    embed_url: null,
    embed_supported: false,
    live_status: 'unknown',
    freshness: 'stale',
    started_at: null,
    last_verified_at: null,
    score: null,
    viewer_count: null,
    location_text: null,
    language: 'en',
  },
];

test('renders one card per stream', () => {
  render(<ResultsList streams={STREAMS} onWatch={vi.fn()} />);
  const rows = screen.getAllByTestId('search-result');
  expect(rows).toHaveLength(2);
  expect(rows[0]).toHaveTextContent('Title A');
  expect(rows[1]).toHaveTextContent('Channel B');
  expect(rows[1]).toHaveTextContent('fake');
  expect(screen.getAllByTestId('stream-card')).toHaveLength(2);
});

test('renders no rows for empty results', () => {
  render(<ResultsList streams={[]} onWatch={vi.fn()} />);
  expect(screen.queryByTestId('search-result')).not.toBeInTheDocument();
});
