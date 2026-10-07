import type { FilterState } from '../lib/filters';

const SORTS = [
  { value: 'relevance', label: 'Most relevant' },
  { value: 'newest', label: 'Newest' },
  { value: 'viewers', label: 'Most viewers' },
];

// Server-side filters (Sprint 5.3). Platform options come from live
// results — never hardcoded — so new adapters appear automatically.
export default function SearchFilters({
  platforms,
  value,
  disabled = false,
  onChange,
}: {
  platforms: string[];
  value: FilterState;
  disabled?: boolean;
  onChange: (next: FilterState) => void;
}) {
  return (
    <div className="search-filters">
      <label>
        Platform{' '}
        <select
          aria-label="Platform"
          value={value.platform}
          disabled={disabled}
          onChange={(e) => onChange({ ...value, platform: e.target.value })}
        >
          <option value="all">All platforms</option>
          {platforms.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </label>
      <label>
        Sort{' '}
        <select
          aria-label="Sort"
          value={value.sort}
          disabled={disabled}
          onChange={(e) => onChange({ ...value, sort: e.target.value })}
        >
          {SORTS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={value.hasLocation}
          disabled={disabled}
          onChange={(e) => onChange({ ...value, hasLocation: e.target.checked })}
        />{' '}
        With location only
      </label>
    </div>
  );
}
