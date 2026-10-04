import type { Stream } from '../types';
import StreamCard from './StreamCard';

export default function ResultsList({ streams }: { streams: Stream[] }) {
  return (
    <ul className="results-list">
      {streams.map((s) => (
        <li key={s.id} data-testid="search-result">
          <StreamCard stream={s} />
        </li>
      ))}
    </ul>
  );
}
