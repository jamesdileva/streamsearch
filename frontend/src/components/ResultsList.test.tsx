import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
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
    source_url: 'https://example.com/a',
    live_status: 'live',
  },
  {
    id: 'b',
    platform: 'fake',
    platform_stream_id: 'b',
    channel_id: 'c-b',
    channel_name: 'Channel B',
    title: 'Title B',
    description: '',
    source_url: 'https://example.com/b',
    live_status: 'unknown',
  },
];

test('renders one row per stream', () => {
  render(<ResultsList streams={STREAMS} />);
  const rows = screen.getAllByTestId('search-result');
  expect(rows).toHaveLength(2);
  expect(rows[0]).toHaveTextContent('Title A');
  expect(rows[1]).toHaveTextContent('Channel B · fake');
});

test('renders no rows for empty results', () => {
  render(<ResultsList streams={[]} />);
  expect(screen.queryByTestId('search-result')).not.toBeInTheDocument();
});
