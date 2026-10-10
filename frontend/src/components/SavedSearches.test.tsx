import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import SavedSearches from './SavedSearches';
import type { SavedSearch } from '../lib/saved-searches';
import { DEFAULT_FILTERS } from '../lib/filters';

const SAVED: SavedSearch[] = [
  { id: 'ss-1', query: 'wildfire near LA', filters: DEFAULT_FILTERS, createdAt: '2026-10-10T00:00:00Z' },
  { id: 'ss-2', query: 'concert tokyo', filters: { ...DEFAULT_FILTERS, sort: 'viewers' }, createdAt: '2026-10-10T01:00:00Z' },
];

test('empty state explains the feature', () => {
  render(
    <SavedSearches
      saved={[]}
      activeId={null}
      onRun={vi.fn()}
      onSave={vi.fn()}
      onRemove={vi.fn()}
    />,
  );
  expect(screen.getByTestId('saved-empty')).toBeInTheDocument();
  expect(screen.queryByTestId('saved-item')).not.toBeInTheDocument();
});

test('renders each saved query with a remove control', () => {
  render(
    <SavedSearches
      saved={SAVED}
      activeId="ss-1"
      onRun={vi.fn()}
      onSave={vi.fn()}
      onRemove={vi.fn()}
    />,
  );
  const items = screen.getAllByTestId('saved-item');
  expect(items).toHaveLength(2);
  expect(items[0]).toHaveTextContent('wildfire near LA');
  expect(items[0]).toHaveClass('saved-item--active');
  expect(
    screen.getByRole('button', { name: 'Remove concert tokyo' }),
  ).toBeInTheDocument();
});

test('run and remove call back with the right ids', () => {
  const onRun = vi.fn();
  const onRemove = vi.fn();
  render(
    <SavedSearches
      saved={SAVED}
      activeId={null}
      onRun={onRun}
      onSave={vi.fn()}
      onRemove={onRemove}
    />,
  );
  fireEvent.click(screen.getByRole('button', { name: 'concert tokyo' }));
  expect(onRun).toHaveBeenCalledWith(SAVED[1]);
  fireEvent.click(screen.getByRole('button', { name: 'Remove wildfire near LA' }));
  expect(onRemove).toHaveBeenCalledWith('ss-1');
});

test('save button calls back', () => {
  const onSave = vi.fn();
  render(
    <SavedSearches
      saved={[]}
      activeId={null}
      onRun={vi.fn()}
      onSave={onSave}
      onRemove={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole('button', { name: 'Save current search' }));
  expect(onSave).toHaveBeenCalledTimes(1);
});
