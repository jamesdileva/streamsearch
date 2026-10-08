import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import WatchModal from './WatchModal';
import type { Stream } from '../types';

const STREAM: Stream = {
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
  language: 'en',
};

afterEach(() => {
  document.body.style.overflow = '';
});

test('renders embed in a labelled modal dialog', () => {
  render(<WatchModal stream={STREAM} onClose={vi.fn()} />);
  const dialog = screen.getByRole('dialog', {
    name: 'Watch: Breaking: storm landfall',
  });
  expect(dialog).toHaveAttribute('aria-modal', 'true');
  const frame = screen.getByTitle('Breaking: storm landfall');
  expect(frame.tagName).toBe('IFRAME');
  expect(frame).toHaveAttribute('src', 'https://www.youtube.com/embed/abc');
  // Playback must never be able to hide the page or steal the referrer.
  expect(frame).toHaveAttribute('allowfullscreen');
  expect(frame).toHaveAttribute(
    'referrerpolicy',
    'strict-origin-when-cross-origin',
  );
});

test('close button closes and takes focus on open', () => {
  const onClose = vi.fn();
  render(<WatchModal stream={STREAM} onClose={onClose} />);
  const close = screen.getByRole('button', { name: 'Close' });
  expect(document.activeElement).toBe(close);
  fireEvent.click(close);
  expect(onClose).toHaveBeenCalledTimes(1);
});

test('escape closes the modal', () => {
  const onClose = vi.fn();
  render(<WatchModal stream={STREAM} onClose={onClose} />);
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(onClose).toHaveBeenCalledTimes(1);
});

test('backdrop click closes but inner click does not', () => {
  const onClose = vi.fn();
  render(<WatchModal stream={STREAM} onClose={onClose} />);
  fireEvent.click(screen.getByTestId('watch-backdrop'));
  expect(onClose).toHaveBeenCalledTimes(1);
  onClose.mockClear();
  fireEvent.click(screen.getByRole('dialog'));
  expect(onClose).not.toHaveBeenCalled();
});

test('background scroll is locked while open', () => {
  render(<WatchModal stream={STREAM} onClose={vi.fn()} />);
  expect(document.body.style.overflow).toBe('hidden');
});

test('falls back to channel name when the title is empty', () => {
  render(
    <WatchModal
      stream={{ ...STREAM, title: '', channel_name: 'News Channel' }}
      onClose={vi.fn()}
    />,
  );
  expect(
    screen.getByRole('dialog', { name: 'Watch: News Channel' }),
  ).toBeInTheDocument();
});
