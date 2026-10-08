import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import SearchFilters from './SearchFilters';
import { DEFAULT_FILTERS } from '../lib/filters';

test('renders platform options from live results, never hardcoded', () => {
  render(
    <SearchFilters
      platforms={['fake', 'twitch']}
      languages={['en']}
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
    <SearchFilters
      platforms={[]}
      languages={[]}
      value={DEFAULT_FILTERS}
      onChange={vi.fn()}
    />,
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

test('language options come from results and never include unknown', () => {
  render(
    <SearchFilters
      platforms={[]}
      languages={['ja', 'en']}
      value={{ ...DEFAULT_FILTERS, language: 'ja' }}
      onChange={vi.fn()}
    />,
  );
  const options = screen
    .getByRole('combobox', { name: 'Language' })
    .querySelectorAll('option');
  // 'All languages' first, then only the languages actually reported.
  expect([...options].map((o) => o.getAttribute('value'))).toEqual([
    '',
    'ja',
    'en',
  ]);
});

test('min viewers input maps a typed number to value', () => {
  const onChange = vi.fn();
  render(
    <SearchFilters
      platforms={[]}
      languages={[]}
      value={DEFAULT_FILTERS}
      onChange={onChange}
    />,
  );
  const input = screen.getByLabelText('Min viewers');
  expect(input).toHaveAttribute('min', '0');
  fireEvent.change(input, { target: { value: '2500' } });
  expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_FILTERS, minViewers: 2500 });
});

test('min viewers input maps blank back to 0', () => {
  const onChange = vi.fn();
  render(
    <SearchFilters
      platforms={[]}
      languages={[]}
      value={{ ...DEFAULT_FILTERS, minViewers: 500 }}
      onChange={onChange}
    />,
  );
  fireEvent.change(screen.getByLabelText('Min viewers'), {
    target: { value: '' },
  });
  expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_FILTERS, minViewers: 0 });
});

test('changes report partial filter state', () => {
  const onChange = vi.fn();
  render(
    <SearchFilters
      platforms={['fake']}
      languages={['en']}
      value={DEFAULT_FILTERS}
      onChange={onChange}
    />,
  );
  fireEvent.change(screen.getByRole('combobox', { name: 'Platform' }), {
    target: { value: 'fake' },
  });
  expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_FILTERS, platform: 'fake' });
  fireEvent.change(screen.getByRole('combobox', { name: 'Language' }), {
    target: { value: 'en' },
  });
  expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_FILTERS, language: 'en' });
  fireEvent.click(screen.getByRole('checkbox'));
  expect(onChange).toHaveBeenCalledWith({
    ...DEFAULT_FILTERS,
    hasLocation: true,
  });
});
