import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import App from './App';
import * as api from './services/api';

beforeEach(() => {
  vi.restoreAllMocks();
});

test('shows backend health when API resolves', async () => {
  vi.spyOn(api, 'fetchHealth').mockResolvedValue({ status: 'ok', env: 'test' });
  render(<App />);
  await waitFor(() =>
    expect(screen.getByTestId('backend-health')).toHaveTextContent('ok'),
  );
});

test('shows error state when API fails', async () => {
  vi.spyOn(api, 'fetchHealth').mockRejectedValue(new Error('down'));
  render(<App />);
  await waitFor(() =>
    expect(screen.getByTestId('backend-error')).toHaveTextContent('down'),
  );
});
