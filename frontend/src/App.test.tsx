import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import App from './App';
import * as api from './services/api';
import type { Stream } from './types';

const STREAM: Stream = {
  id: 'fake-1',
  platform: 'fake',
  platform_stream_id: 'fake-1',
  channel_id: 'fake-channel-1',
  channel_name: 'Skeleton Channel',
  title: 'Skeleton live: skeleton',
  description: 'fixture',
  source_url: 'https://example.com/watch/fake-1',
  live_status: 'live',
};

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api, 'fetchHealth').mockResolvedValue({
    status: 'ok',
    env: 'test',
  });
  vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'skeleton',
    results: [STREAM],
    count: 1,
  });
});

test('shows backend health when API resolves', async () => {
  render(<App />);
  await waitFor(() =>
    expect(screen.getByTestId('backend-health')).toHaveTextContent('ok'),
  );
});

test('shows error state when API fails', async () => {
  vi.spyOn(api, 'fetchHealth').mockRejectedValue(new Error('down'));
  render(<App />);
  await waitFor(() =>
    expect(screen.getByTestId('backend-error')).toHaveTextContent('down'),
  );
});

test('renders normalized fake stream fields', async () => {
  render(<App />);
  const el = await screen.findByTestId('skeleton-stream');
  expect(el).toHaveTextContent('[live] Skeleton live: skeleton');
  expect(el).toHaveTextContent('Skeleton Channel · fake');
});

test('shows empty preview when no results', async () => {
  vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'skeleton',
    results: [],
    count: 0,
  });
  render(<App />);
  await waitFor(() =>
    expect(screen.getByTestId('skeleton-empty')).toBeInTheDocument(),
  );
});
