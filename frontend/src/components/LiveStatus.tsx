import type { Stream } from '../types';

const LABEL = { live: 'LIVE', ended: 'Ended', unknown: 'Unknown' } as const;

export default function LiveStatus({
  status,
}: {
  status: Stream['live_status'];
}) {
  return (
    <span
      className={`live-status live-status--${status}`}
      data-testid="live-status"
    >
      <span aria-hidden="true">{status === 'live' ? '●' : '○'}</span>{' '}
      {LABEL[status]}
    </span>
  );
}
