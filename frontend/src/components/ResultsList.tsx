import type { Stream } from '../types';
import StreamCard from './StreamCard';

// Thin wrapper so cards stay dumb: this only maps a stream to its handler.
export default function ResultsList({
  streams,
  onWatch,
}: {
  streams: Stream[];
  onWatch: (stream: Stream) => void;
}) {
  return (
    <ul className="results-list">
      {streams.map((s) => (
        <li key={s.id} data-testid="search-result">
          <StreamCard stream={s} onWatch={onWatch} />
        </li>
      ))}
    </ul>
  );
}
