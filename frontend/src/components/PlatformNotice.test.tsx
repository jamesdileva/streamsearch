import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import PlatformNotice from './PlatformNotice';
import type { PlatformStatus } from '../types';

const OK: PlatformStatus = { platform: 'youtube', status: 'ok' };
const BAD: PlatformStatus = {
  platform: 'twitch',
  status: 'error',
  detail: 'rate limited (429)',
};

test('renders nothing when every platform is healthy', () => {
  render(<PlatformNotice statuses={[OK, { platform: 'kick', status: 'ok' }]} />);
  expect(screen.queryByTestId('platform-notice')).not.toBeInTheDocument();
});

test('warns about a partial outage without hiding results', () => {
  render(<PlatformNotice statuses={[OK, BAD]} />);
  const notice = screen.getByTestId('platform-notice');
  expect(notice).toHaveTextContent(
    'Showing results from 1 of 2 platforms — twitch unavailable right now.',
  );
  expect(notice).toHaveAttribute('role', 'status');
});

test('reports a total outage', () => {
  render(<PlatformNotice statuses={[BAD, { platform: 'kick', status: 'error' }]} />);
  expect(screen.getByTestId('platform-notice')).toHaveTextContent(
    'Live search is unavailable right now (twitch, kick).',
  );
});
