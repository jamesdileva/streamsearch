import { useState, type FormEvent } from 'react';
import { submitReport } from '../services/api';
import type { ReportReason } from '../types';

const REASONS: { value: ReportReason; label: string }[] = [
  { value: 'broken_link', label: 'Broken link' },
  { value: 'no_longer_live', label: 'No longer live' },
  { value: 'wrong_topic', label: 'Wrong topic' },
  { value: 'other', label: 'Other' },
];

type Phase =
  | { name: 'closed' }
  | { name: 'open' }
  | { name: 'sending' }
  | { name: 'sent' }
  | { name: 'error'; message: string };

// Per-card correction affordance. Reports feed the server-side store
// (POST /api/reports); moderation tooling is out of scope for Sprint 2.3.
export default function ReportButton({
  streamId,
  platform,
}: {
  streamId: string;
  platform: string;
}) {
  const [phase, setPhase] = useState<Phase>({ name: 'closed' });
  const [reason, setReason] = useState<ReportReason>('broken_link');
  const [detail, setDetail] = useState('');

  const send = (e: FormEvent) => {
    e.preventDefault();
    setPhase({ name: 'sending' });
    submitReport({ stream_id: streamId, platform, reason, detail })
      .then(() => setPhase({ name: 'sent' }))
      .catch((err: unknown) =>
        setPhase({
          name: 'error',
          message: err instanceof Error ? err.message : 'unknown error',
        }),
      );
  };

  if (phase.name === 'closed') {
    return (
      <button type="button" onClick={() => setPhase({ name: 'open' })}>
        Report
      </button>
    );
  }

  if (phase.name === 'sent') {
    return <p data-testid="report-sent">Thanks — report received.</p>;
  }

  return (
    <form onSubmit={send} className="report-form" aria-label="report stream">
      <fieldset disabled={phase.name === 'sending'}>
        <legend>Report this stream</legend>
        {REASONS.map((r) => (
          <label key={r.value}>
            <input
              type="radio"
              name="reason"
              value={r.value}
              checked={reason === r.value}
              onChange={() => setReason(r.value)}
            />
            {r.label}
          </label>
        ))}
        <label>
          Details (optional)
          <input
            type="text"
            value={detail}
            maxLength={500}
            onChange={(e) => setDetail(e.target.value)}
            placeholder="What is wrong?"
          />
        </label>
      </fieldset>
      {phase.name === 'error' && (
        <p data-testid="report-error">Report failed: {phase.message}</p>
      )}
      <button type="submit" disabled={phase.name === 'sending'}>
        {phase.name === 'sending' ? 'Sending…' : 'Submit report'}
      </button>
      <button
        type="button"
        disabled={phase.name === 'sending'}
        onClick={() => setPhase({ name: 'closed' })}
      >
        Cancel
      </button>
    </form>
  );
}
