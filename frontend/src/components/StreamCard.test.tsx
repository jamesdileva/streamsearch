import { render, screen, within } from '@testing-library/react';
import { expect, test } from 'vitest';
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
  score: null,
};

test('full record shows every card element', () => {
  render(<StreamCard stream={FULL} />);
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

  const watch = within(card).getByRole('link', { name: 'Watch' });
  expect(watch).toHaveAttribute(
    'href',
    'https://www.youtube.com/embed/abc',
  );
  expect(watch).toHaveAttribute('target', '_blank');
  const source = within(card).getByRole('link', { name: 'Open Source' });
  expect(source).toHaveAttribute(
    'href',
    'https://www.youtube.com/watch?v=abc',
  );
});

test('minimal record omits everything unavailable', () => {
  render(<StreamCard stream={MINIMAL} />);
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
  render(<StreamCard stream={{ ...FULL, live_status: 'ended' }} />);
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
    />,
  );
  expect(screen.getByTestId('live-freshness')).toHaveTextContent(
    'Aging · verified 12m ago',
  );
});
