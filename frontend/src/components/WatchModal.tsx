import { useEffect, useRef } from 'react';
import type { Stream } from '../types';

// Full-screen embed playback (Sprint 8.3). Discovery stays separate from
// playback: the modal is the only place an embed iframe ever appears.
export default function WatchModal({
  stream,
  onClose,
}: {
  stream: Stream;
  onClose: () => void;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    // Lock background scrolling while the modal is open.
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  return (
    <div
      className="watch-backdrop"
      data-testid="watch-backdrop"
      onClick={() => onClose()}
    >
      <div
        className="watch-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`Watch: ${stream.title || stream.channel_name}`}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          ref={closeRef}
          type="button"
          className="watch-close"
          aria-label="Close"
          onClick={() => onClose()}
        >
          Close
        </button>
        <iframe
          className="watch-frame"
          src={stream.embed_url as string}
          title={stream.title || stream.channel_name}
          allow="autoplay; fullscreen; picture-in-picture"
          allowFullScreen
          referrerPolicy="strict-origin-when-cross-origin"
        />
      </div>
    </div>
  );
}
