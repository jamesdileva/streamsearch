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
  language: 'en',
  location_text: null,
  score: null,
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
    duplicates_removed: 0,
    platform_status: [{ platform: 'fake', status: 'ok' }],
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
  await waitFor(() => expect(search).toHaveBeenCalled());
  expect(search.mock.calls[0][0]).toBe(long);
  expect(await screen.findAllByTestId('search-result')).toHaveLength(1);
});

test('special characters pass through unmodified', async () => {
  const special = 'wildfire & <smoke> "LA" #live?';
  const search = vi.spyOn(api, 'searchStreams');
  render(<App />);
  submitQuery(special);
  await waitFor(() => expect(search).toHaveBeenCalled());
  expect(search.mock.calls[0][0]).toBe(special);
  expect(await screen.findAllByTestId('search-result')).toHaveLength(1);
});

test('repeated searches show the latest results', async () => {
  const second: Stream = { ...STREAM, id: 'fake-2', title: 'Second result' };
  const search = vi.spyOn(api, 'searchStreams');
  search.mockResolvedValueOnce({
    query: 'one',
    results: [STREAM],
    count: 1,
    duplicates_removed: 0,
    platform_status: [{ platform: 'fake', status: 'ok' }],
  });
  search.mockResolvedValueOnce({
    query: 'two',
    results: [second],
    count: 1,
    duplicates_removed: 0,
    platform_status: [{ platform: 'fake', status: 'ok' }],
  });
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
  expect(search.mock.calls[1][0]).toBe('two');
});

test('empty results show the empty state', async () => {
  vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'nothing',
    results: [],
    count: 0,
    duplicates_removed: 0,
    platform_status: [{ platform: 'fake', status: 'ok' }],
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

test('platform options come from results and refetch on change', async () => {
  const twitch: Stream = {
    ...STREAM,
    id: 'twitch-1',
    platform: 'twitch',
    platform_stream_id: '1',
    title: 'Twitch live',
  };
  const search = vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'wildfire',
    results: [STREAM, twitch],
    count: 2,
    duplicates_removed: 0,
    platform_status: [{ platform: 'fake', status: 'ok' }],
  });
  render(<App />);
  submitQuery('wildfire');
  await screen.findAllByTestId('search-result');
  const options = screen
    .getByRole('combobox', { name: 'Platform' })
    .querySelectorAll('option');
  expect([...options].map((o) => o.getAttribute('value'))).toEqual([
    'all',
    'fake',
    'twitch',
  ]);
  fireEvent.change(screen.getByRole('combobox', { name: 'Platform' }), {
    target: { value: 'twitch' },
  });
  await waitFor(() => expect(search).toHaveBeenCalledTimes(2));
  expect(search.mock.calls[1][0]).toBe('wildfire');
  expect(search.mock.calls[1][1]).toMatchObject({ platform: 'twitch' });
});

test('sort and location changes refetch the active query', async () => {
  const search = vi.spyOn(api, 'searchStreams');
  render(<App />);
  submitQuery('wildfire');
  await screen.findAllByTestId('search-result');
  fireEvent.change(screen.getByRole('combobox', { name: 'Sort' }), {
    target: { value: 'viewers' },
  });
  await waitFor(() => expect(search).toHaveBeenCalledTimes(2));
  expect(search.mock.calls[1][1]).toMatchObject({ sort: 'viewers' });
  fireEvent.click(screen.getByRole('checkbox'));
  await waitFor(() => expect(search).toHaveBeenCalledTimes(3));
  expect(search.mock.calls[2][1]).toMatchObject({ hasLocation: true });
});

test('filter changes before any search do not fetch', () => {
  const search = vi.spyOn(api, 'searchStreams');
  render(<App />);
  fireEvent.change(screen.getByRole('combobox', { name: 'Sort' }), {
    target: { value: 'newest' },
  });
  expect(search).not.toHaveBeenCalled();
});

test('language options come from results and refetch on change', async () => {
  const ja: Stream = {
    ...STREAM,
    id: 'fake-2',
    platform_stream_id: 'fake-2',
    title: 'Japanese live',
    language: 'ja',
  };
  const unknown: Stream = {
    ...STREAM,
    id: 'fake-3',
    platform_stream_id: 'fake-3',
    title: 'No language reported',
    language: null,
  };
  const search = vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'wildfire',
    results: [STREAM, ja, unknown],
    count: 3,
    duplicates_removed: 0,
    platform_status: [{ platform: 'fake', status: 'ok' }],
  });
  render(<App />);
  submitQuery('wildfire');
  await screen.findAllByTestId('search-result');

  const options = screen
    .getByRole('combobox', { name: 'Language' })
    .querySelectorAll('option');
  // Only reported languages appear — 'null' never becomes an option.
  expect([...options].map((o) => o.getAttribute('value'))).toEqual(['', 'en', 'ja']);

  fireEvent.change(screen.getByRole('combobox', { name: 'Language' }), {
    target: { value: 'ja' },
  });
  await waitFor(() => expect(search).toHaveBeenCalledTimes(2));
  expect(search.mock.calls[1][1]).toMatchObject({ language: 'ja' });
});

test('min viewers change refetches with the numeric floor', async () => {
  const search = vi.spyOn(api, 'searchStreams');
  render(<App />);
  submitQuery('wildfire');
  await screen.findAllByTestId('search-result');
  fireEvent.change(screen.getByLabelText('Min viewers'), {
    target: { value: '500' },
  });
  await waitFor(() => expect(search).toHaveBeenCalledTimes(2));
  expect(search.mock.calls[1][1]).toMatchObject({ minViewers: 500 });
});
test('watch button opens and closes the full-screen player', async () => {
  const watchable: Stream = {
    ...STREAM,
    embed_supported: true,
    embed_url: 'https://www.youtube.com/embed/fake-1',
  };
  vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'wildfire',
    results: [watchable],
    count: 1,
    duplicates_removed: 0,
    platform_status: [{ platform: 'fake', status: 'ok' }],
  });
  render(<App />);
  submitQuery('wildfire');
  fireEvent.click(await screen.findByTestId('watch-button'));

  const dialog = await screen.findByRole('dialog');
  expect(dialog).toHaveAttribute('aria-modal', 'true');
  expect(screen.getByTitle('Skeleton live: wildfire')).toHaveAttribute(
    'src',
    'https://www.youtube.com/embed/fake-1',
  );

  fireEvent.keyDown(document, { key: 'Escape' });
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
});

test('partial outage shows a notice but keeps healthy results', async () => {
  const twitch: Stream = {
    ...STREAM,
    id: 'fake-2',
    platform_stream_id: 'fake-2',
    title: 'Twitch live',
  };
  vi.spyOn(api, 'searchStreams').mockResolvedValue({
    query: 'wildfire',
    results: [STREAM, twitch],
    count: 2,
    duplicates_removed: 0,
    platform_status: [
      { platform: 'fake', status: 'ok' },
      { platform: 'twitch', status: 'error', detail: 'rate limited (429)' },
    ],
  });
  render(<App />);
  submitQuery('wildfire');
  await screen.findAllByTestId('search-result');
  expect(screen.getByTestId('platform-notice')).toHaveTextContent(
    'Showing results from 1 of 2 platforms',
  );
});
