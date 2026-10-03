import type { Stream } from '../types';

// Minimal result rows for Sprint 1.1. Polished cards land in Sprint 2.1.
export default function ResultsList({ streams }: { streams: Stream[] }) {
  return (
    <ul className="results-list">
      {streams.map((s) => (
        <li key={s.id} data-testid="search-result" className="result-row">
          <p>
            [{s.live_status}] {s.title}
          </p>
          <p>
            {s.channel_name} · {s.platform}
          </p>
        </li>
      ))}
    </ul>
  );
}
