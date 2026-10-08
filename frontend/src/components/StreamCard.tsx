import { Fragment, type ReactNode } from 'react';
import type { Stream } from '../types';
import LiveStatus from './LiveStatus';
import PlatformBadge from './PlatformBadge';
import ReportButton from './ReportButton';

// Restrained card: every field comes from the normalized Stream model.
// Anything the platform didn't provide is simply omitted ("where available").
export default function StreamCard({
  stream,
  onWatch,
}: {
  stream: Stream;
  onWatch: (stream: Stream) => void;
}) {
  const details: ReactNode[] = [];
  if (stream.started_at) {
    const when = new Date(stream.started_at);
    if (!Number.isNaN(when.getTime())) {
      details.push(
        <time dateTime={stream.started_at}>{when.toLocaleString()}</time>,
      );
    }
  }
  if (stream.viewer_count != null) {
    details.push(
      <span>{stream.viewer_count.toLocaleString('en-US')} watching</span>,
    );
  }
  if (stream.location_text) {
    details.push(<span>{stream.location_text}</span>);
  }

  const canWatch = stream.embed_supported && stream.embed_url;

  return (
    <article className="stream-card" data-testid="stream-card">
      {stream.thumbnail_url ? (
        <img
          className="stream-thumb"
          src={stream.thumbnail_url}
          alt=""
          loading="lazy"
          data-testid="stream-thumb"
        />
      ) : (
        <div
          className="stream-thumb stream-thumb--empty"
          data-testid="stream-thumb-empty"
          aria-hidden="true"
        />
      )}
      <div className="stream-body">
        <div className="stream-top">
          <LiveStatus
            status={stream.live_status}
            freshness={stream.freshness}
            verifiedAt={stream.last_verified_at}
          />
          <PlatformBadge platform={stream.platform} />
        </div>
        <h3 className="stream-title">
          {stream.title || 'Untitled stream'}
        </h3>
        <p className="stream-channel">
          {stream.channel_name || 'Unknown channel'}
        </p>
        {details.length > 0 && (
          <p className="stream-meta">
            {details.map((d, i) => (
              <Fragment key={i}>
                {i > 0 && ' · '}
                {d}
              </Fragment>
            ))}
          </p>
        )}
        {(canWatch || stream.source_url) && (
          <div className="stream-actions">
            {canWatch && (
              <button
                type="button"
                className="watch-button"
                data-testid="watch-button"
                onClick={() => onWatch(stream)}
              >
                Watch
              </button>
            )}
            {stream.source_url && (
              <a href={stream.source_url} target="_blank" rel="noreferrer">
                Open Source
              </a>
            )}
          </div>
        )}
        <div className="stream-report">
          <ReportButton
            streamId={stream.platform_stream_id}
            platform={stream.platform}
          />
        </div>
      </div>
    </article>
  );
}
