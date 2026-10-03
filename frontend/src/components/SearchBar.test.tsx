import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import SearchBar from './SearchBar';

test('submits the typed query', () => {
  const onSearch = vi.fn();
  render(<SearchBar onSearch={onSearch} />);
  fireEvent.change(screen.getByRole('searchbox'), {
    target: { value: 'concert' },
  });
  fireEvent.submit(screen.getByRole('search'));
  expect(onSearch).toHaveBeenCalledWith('concert');
});

test('disables input and button while loading', () => {
  render(<SearchBar isLoading onSearch={vi.fn()} />);
  expect(screen.getByRole('searchbox')).toBeDisabled();
  const button = screen.getByRole('button', { name: /searching/i });
  expect(button).toBeDisabled();
});
