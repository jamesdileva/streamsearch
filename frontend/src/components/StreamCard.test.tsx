import { fireEvent, render, screen, within } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import StreamCard from './StreamCard';
import type { Stream } from '../types';

const FULL: Stream = {
  id: 'youtube-abc',
  platform: 'youtube',
  platform_stream_id: 'abc',
  channel_id: 'chan-1',
  channel_name: 'News Channel',
  title: 'Breaking: storm landfall',
  description: 'Live coverage.',
  thumbnail_url: 'https://img/high.jpg',
  source_url: 'https://www.youtube.com/watch?v=abc',
  embed_url: 'https://www.youtube.com/embed/abc',
  embed_supported: true,
  live_status: 'live',
  freshness: 'fresh',
  started_at: '2026-10-04T00:00:00Z',
  last_verified_at: new Date().toISOString(),
  viewer_count: 1234,
  location_text: 'Florida',
  language: 'en',
  score: 160.0,
};

const MINIMAL: Stream = {
  id: 'fake-1',
  platform: 'fake',
  platform_stream_id: 'fake-1',
  channel_id: '',
  channel_name: '',
  title: '',
  description: '',
  thumbnail_url: '',
  source_url: '',
  embed_url: null,
  embed_supported: false,
  live_status: 'unknown',
  freshness: 'stale',
  started_at: null,
  last_verified_at: null,
  viewer_count: null,
  location_text: null,
  language: 'en',
  score: null,
};

test('full record shows every card element', () => {
  const onWatch = vi.fn();
  render(<StreamCard stream={FULL} onWatch={onWatch} />);
  const card = screen.getByTestId('stream-card');

  expect(within(card).getByTestId('live-status')).toHaveTextContent('LIVE');
  expect(within(card).getByTestId('live-freshness')).toHaveTextContent(
    'Fresh',
  );
  expect(within(card).getByTestId('platform-badge')).toHaveTextContent(
    'youtube',
  );
  expect(
    within(card).getByText('Breaking: storm landfall'),
  ).toBeInTheDocument();
  expect(within(card).getByText('News Channel')).toBeInTheDocument();

  const img = within(card).getByTestId('stream-thumb');
  expect(img).toHaveAttribute('src', 'https://img/high.jpg');

  const time = within(card).getByText(/2026/, { selector: 'time' });
  expect(time).toHaveAttribute('datetime', '2026-10-04T00:00:00Z');

  expect(within(card).getByText('1,234 watching')).toBeInTheDocument();
  expect(within(card).getByText('Florida')).toBeInTheDocument();

  const watch = within(card).getByTestId('watch-button');
  fireEvent.click(watch);
  // Playback is opt-in per the design: no auto-navigation, no new tab.
  expect(onWatch).toHaveBeenCalledTimes(1);
  expect(onWatch.mock.calls[0][0]).toBe(FULL);
  const source = within(card).getByRole('link', { name: 'Open Source' });
  expect(source).toHaveAttribute(
    'href',
    'https://www.youtube.com/watch?v=abc',
  );
});

test('watch button is absent when embedding is unsupported', () => {
  render(
    <StreamCard stream={{ ...FULL, embed_supported: false }} onWatch={vi.fn()} />,
  );
  expect(screen.queryByTestId('watch-button')).not.toBeInTheDocument();
});

test('minimal record omits everything unavailable', () => {
  render(<StreamCard stream={MINIMAL} onWatch={vi.fn()} />);
  const card = screen.getByTestId('stream-card');

  expect(within(card).getByTestId('live-status')).toHaveTextContent('Unknown');
  expect(within(card).getByTestId('live-freshness')).toHaveTextContent(
    'Stale · not verified',
  );
  expect(
    within(card).getByTestId('stream-thumb-empty'),
  ).toBeInTheDocument();
  expect(within(card).queryByTestId('stream-thumb')).not.toBeInTheDocument();
  expect(within(card).getByText('Untitled stream')).toBeInTheDocument();
  expect(within(card).getByText('Unknown channel')).toBeInTheDocument();
  expect(within(card).queryByText(/watching/)).not.toBeInTheDocument();
  expect(within(card).queryByRole('link')).not.toBeInTheDocument();
});

test('ended record shows ended status without live styling', () => {
  render(<StreamCard stream={{ ...FULL, live_status: 'ended' }} onWatch={vi.fn()} />);
  const badge = screen.getByTestId('live-status');
  expect(badge).toHaveTextContent('Ended');
  expect(badge).toHaveClass('live-status--ended');
  expect(
    within(screen.getByTestId('stream-card')).queryByTestId('live-freshness'),
  ).not.toBeInTheDocument();
});

test('aging record shows verified age', () => {
  const twelveMinAgo = new Date(Date.now() - 12 * 60_000).toISOString();
  render(
    <StreamCard
      stream={{ ...FULL, freshness: 'aging', last_verified_at: twelveMinAgo }}
      onWatch={vi.fn()}
    />,
  );
  expect(screen.getByTestId('live-freshness')).toHaveTextContent(
    'Aging · verified 12m ago',
  );
});
