import type { Stream } from '../types';

export default function PlatformBadge({
  platform,
}: {
  platform: Stream['platform'];
}) {
  return (
    <span className="platform-badge" data-testid="platform-badge">
      {platform}
    </span>
  );
}
