import { expect, test } from 'vitest';
import { formatAge } from './time';

const NOW = Date.parse('2026-10-04T00:00:00Z');
const iso = (msAgo: number) => new Date(NOW - msAgo).toISOString();

test('formats sub-minute and future as just now', () => {
  expect(formatAge(iso(30_000), NOW)).toBe('just now');
  expect(formatAge(new Date(NOW + 30_000).toISOString(), NOW)).toBe('just now');
});

test('formats minutes, hours, days', () => {
  expect(formatAge(iso(90_000), NOW)).toBe('1m');
  expect(formatAge(iso(12 * 60_000), NOW)).toBe('12m');
  expect(formatAge(iso(3 * 3_600_000), NOW)).toBe('3h');
  expect(formatAge(iso(2 * 86_400_000), NOW)).toBe('2d');
});
