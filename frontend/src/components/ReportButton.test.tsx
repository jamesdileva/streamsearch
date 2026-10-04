import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import ReportButton from './ReportButton';
import * as api from '../services/api';
import type { ReportReason } from '../types';

beforeEach(() => {
  vi.restoreAllMocks();
});

function openForm() {
  render(<ReportButton streamId="vid-1" platform="youtube" />);
  fireEvent.click(screen.getByRole('button', { name: 'Report' }));
}

test('opens a form with all four reasons', () => {
  openForm();
  for (const label of [
    'Broken link',
    'No longer live',
    'Wrong topic',
    'Other',
  ]) {
    expect(screen.getByLabelText(label)).toBeInTheDocument();
  }
});

test.each([
  ['broken_link', 'Broken link'],
  ['no_longer_live', 'No longer live'],
  ['wrong_topic', 'Wrong topic'],
  ['other', 'Other'],
] as [ReportReason, string][])('submits reason %s', async (value, label) => {
  const submit = vi
    .spyOn(api, 'submitReport')
    .mockResolvedValue(undefined);
  openForm();
  fireEvent.click(screen.getByLabelText(label));
  fireEvent.submit(screen.getByRole('form', { name: 'report stream' }));
  await waitFor(() =>
    expect(submit).toHaveBeenCalledWith({
      stream_id: 'vid-1',
      platform: 'youtube',
      reason: value,
      detail: '',
    }),
  );
  await waitFor(() =>
    expect(screen.getByTestId('report-sent')).toBeInTheDocument(),
  );
});

test('includes optional details', async () => {
  const submit = vi
    .spyOn(api, 'submitReport')
    .mockResolvedValue(undefined);
  openForm();
  fireEvent.change(screen.getByPlaceholderText('What is wrong?'), {
    target: { value: 'ended an hour ago' },
  });
  fireEvent.submit(screen.getByRole('form', { name: 'report stream' }));
  await waitFor(() =>
    expect(submit).toHaveBeenCalledWith(
      expect.objectContaining({ detail: 'ended an hour ago' }),
    ),
  );
});

test('shows error state when submit fails', async () => {
  vi.spyOn(api, 'submitReport').mockRejectedValue(new Error('down'));
  openForm();
  fireEvent.submit(screen.getByRole('form', { name: 'report stream' }));
  await waitFor(() =>
    expect(screen.getByTestId('report-error')).toHaveTextContent('down'),
  );
});

test('cancel closes the form', () => {
  openForm();
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(
    screen.queryByRole('form', { name: 'report stream' }),
  ).not.toBeInTheDocument();
});
