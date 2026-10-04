import type { Freshness, Stream } from '../types';
import { formatAge } from '../lib/time';

const STATUS_LABEL = { live: 'LIVE', ended: 'Ended', unknown: 'Unknown' } as const;
const FRESH_LABEL: Record<Freshness, string> = {
  fresh: 'Fresh',
  aging: 'Aging',
  stale: 'Stale',
  ended: 'Ended',
};

// Status badge + trust note: what the platform claims, and how much
// we trust the claim. Ended is terminal and needs no freshness note.
export default function LiveStatus({
  status,
  freshness,
  verifiedAt,
}: {
  status: Stream['live_status'];
  freshness: Stream['freshness'];
  verifiedAt: Stream['last_verified_at'];
}) {
  let note: string | null = null;
  if (status !== 'ended' && freshness && freshness !== 'fresh') {
    note = FRESH_LABEL[freshness];
    if (verifiedAt) {
      note += ` · verified ${formatAge(verifiedAt)} ago`;
    } else if (freshness === 'stale') {
      note += ' · not verified';
    }
  } else if (status !== 'ended' && freshness === 'fresh') {
    note = 'Fresh';
  }

  return (
    <span
      className={`live-status live-status--${status}`}
      data-testid="live-status"
    >
      <span aria-hidden="true">{status === 'live' ? '●' : '○'}</span>{' '}
      {STATUS_LABEL[status]}
      {note && (
        <span className="live-freshness" data-testid="live-freshness">
          {' · '}
          {note}
        </span>
      )}
    </span>
  );
}
