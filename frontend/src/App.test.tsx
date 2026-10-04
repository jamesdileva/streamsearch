import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
  title: 'Skeleton live: wildfire',
  description: 'fixture',
  thumbnail_url: '',
  source_url: 'https://example.com/watch/fake-1',
  embed_url: null,
  embed_supported: false,
  live_status: 'live',
  freshness: 'fresh',
  started_at: null,
  last_verified_at: new Date().toISOString(),
  viewer_count: null,
  location_text: null,
};

function submitQuery(value: string) {
  fireEvent.change(screen.getByRole('searchbox'), {
    target: { value },
  });
  fireEvent.submit(screen.getByRole('search'));
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(api, 'fetchHealth').mockResolvedValue({
    status: 'ok',
    env: 'test',
  });
  vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'wildfire',
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

test('shows backend error state when health fails', async () => {
  vi.spyOn(api, 'fetchHealth').mockRejectedValue(new Error('down'));
  render(<App />);
  await waitFor(() =>
    expect(screen.getByTestId('backend-error')).toHaveTextContent('down'),
  );
});

test('empty query shows hint and never calls the API', async () => {
  const search = vi.spyOn(api, 'searchStreams');
  render(<App />);
  submitQuery('   ');
  await waitFor(() =>
    expect(screen.getByTestId('search-hint')).toBeInTheDocument(),
  );
  expect(search).not.toHaveBeenCalled();
});

test('normal query renders results', async () => {
  render(<App />);
  submitQuery('wildfire');
  const rows = await screen.findAllByTestId('search-result');
  expect(rows).toHaveLength(1);
  expect(rows[0]).toHaveTextContent('Skeleton live: wildfire');
  expect(rows[0]).toHaveTextContent('Skeleton Channel');
  expect(
    screen.getByTestId('search-count'),
  ).toHaveTextContent('Found 1 live stream');
});

test('long query passes through to the API', async () => {
  const long = 'storm '.repeat(100).trim();
  const search = vi.spyOn(api, 'searchStreams');
  render(<App />);
  submitQuery(long);
  await waitFor(() => expect(search).toHaveBeenCalledWith(long));
  expect(await screen.findAllByTestId('search-result')).toHaveLength(1);
});

test('special characters pass through unmodified', async () => {
  const special = 'wildfire & <smoke> "LA" #live?';
  const search = vi.spyOn(api, 'searchStreams');
  render(<App />);
  submitQuery(special);
  await waitFor(() => expect(search).toHaveBeenCalledWith(special));
  expect(await screen.findAllByTestId('search-result')).toHaveLength(1);
});

test('repeated searches show the latest results', async () => {
  const second: Stream = { ...STREAM, id: 'fake-2', title: 'Second result' };
  const search = vi.spyOn(api, 'searchStreams');
  search.mockResolvedValueOnce({ query: 'one', results: [STREAM], count: 1 });
  search.mockResolvedValueOnce({ query: 'two', results: [second], count: 1 });
  render(<App />);
  submitQuery('one');
  await waitFor(() => {
    const rows = screen.getAllByTestId('search-result');
    expect(rows).toHaveLength(1);
    expect(rows[0]).toHaveTextContent('Skeleton live: wildfire');
  });
  submitQuery('two');
  await waitFor(() => {
    const rows = screen.getAllByTestId('search-result');
    expect(rows).toHaveLength(1);
    expect(rows[0]).toHaveTextContent('Second result');
  });
  expect(search).toHaveBeenCalledTimes(2);
  expect(search).toHaveBeenLastCalledWith('two');
});

test('empty results show the empty state', async () => {
  vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'nothing',
    results: [],
    count: 0,
  });
  render(<App />);
  submitQuery('nothing');
  await waitFor(() =>
    expect(screen.getByTestId('search-empty')).toHaveTextContent(
      'No live streams found',
    ),
  );
});

test('failed search shows the error state', async () => {
  vi.spyOn(api, 'searchStreams').mockRejectedValue(new Error('boom'));
  render(<App />);
  submitQuery('wildfire');
  await waitFor(() =>
    expect(screen.getByTestId('search-error')).toHaveTextContent('boom'),
  );
});
