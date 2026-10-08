import type { FilterState } from '../lib/filters';

const SORTS = [
  { value: 'relevance', label: 'Most relevant' },
  { value: 'newest', label: 'Newest' },
  { value: 'viewers', label: 'Most viewers' },
];

// Server-side filters (Sprint 5.3, extended 8.1). Platform and language
// options come from live results — never hardcoded — so new adapters and
// languages appear automatically.
export default function SearchFilters({
  platforms,
  languages,
  value,
  disabled = false,
  onChange,
}: {
  platforms: string[];
  languages: string[];
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
        Language{' '}
        <select
          aria-label="Language"
          value={value.language}
          disabled={disabled}
          onChange={(e) => onChange({ ...value, language: e.target.value })}
        >
          <option value="">All languages</option>
          {languages.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </label>
      <label>
        Min viewers{' '}
        <input
          type="number"
          min={0}
          step={100}
          aria-label="Min viewers"
          value={value.minViewers === 0 ? '' : String(value.minViewers)}
          placeholder="0"
          disabled={disabled}
          onChange={(e) => {
            const raw = e.target.value.trim();
            onChange({
              ...value,
              minViewers: raw === '' ? 0 : Number(raw),
            });
          }}
        />
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
