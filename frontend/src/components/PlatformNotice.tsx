import type { PlatformStatus } from '../types';

// Partial-outage notice (Sprint 10.1). Results from healthy platforms are
// still valid, so this warns without hiding them. Absent when everything
// is healthy.
export default function PlatformNotice({
  statuses,
}: {
  statuses: PlatformStatus[];
}) {
  const degraded = statuses.filter((s) => s.status === 'error');
  if (degraded.length === 0) return null;

  const names = degraded.map((s) => s.platform).join(', ');
  const total = statuses.length;
  const healthy = total - degraded.length;

  return (
    <p className="platform-notice" role="status" data-testid="platform-notice">
      {healthy > 0
        ? `Showing results from ${healthy} of ${total} platforms — ${names} unavailable right now.`
        : `Live search is unavailable right now (${names}).`}
    </p>
  );
}
