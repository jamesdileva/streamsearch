import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import SearchFilters from './SearchFilters';
import { DEFAULT_FILTERS } from '../lib/filters';

test('renders platform options from live results, never hardcoded', () => {
  render(
    <SearchFilters
      platforms={['fake', 'twitch']}
      value={DEFAULT_FILTERS}
      onChange={vi.fn()}
    />,
  );
  const options = screen
    .getByRole('combobox', { name: 'Platform' })
    .querySelectorAll('option');
  expect([...options].map((o) => o.textContent)).toEqual([
    'All platforms',
    'fake',
    'twitch',
  ]);
});

test('sort offers relevance, newest, viewers', () => {
  render(
    <SearchFilters platforms={[]} value={DEFAULT_FILTERS} onChange={vi.fn()} />,
  );
  const options = screen
    .getByRole('combobox', { name: 'Sort' })
    .querySelectorAll('option');
  expect([...options].map((o) => o.getAttribute('value'))).toEqual([
    'relevance',
    'newest',
    'viewers',
  ]);
});

test('changes report partial filter state', () => {
  const onChange = vi.fn();
  render(
    <SearchFilters platforms={['fake']} value={DEFAULT_FILTERS} onChange={onChange} />,
  );
  fireEvent.change(screen.getByRole('combobox', { name: 'Platform' }), {
    target: { value: 'fake' },
  });
  expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_FILTERS, platform: 'fake' });
  fireEvent.click(screen.getByRole('checkbox'));
  expect(onChange).toHaveBeenCalledWith({
    ...DEFAULT_FILTERS,
    hasLocation: true,
  });
});
