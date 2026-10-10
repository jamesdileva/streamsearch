import type { SavedSearch } from '../lib/saved-searches';

// Reads from a plain array so the component stays presentation-only;
// persistence lives in lib/saved-searches and App state.
export default function SavedSearches({
  saved,
  activeId,
  disabled = false,
  onRun,
  onSave,
  onRemove,
}: {
  saved: SavedSearch[];
  activeId: string | null;
  disabled?: boolean;
  onRun: (saved: SavedSearch) => void;
  onSave: () => void;
  onRemove: (id: string) => void;
}) {
  return (
    <section className="saved-searches" aria-label="Saved searches">
      <div className="saved-searches__head">
        <h2>Saved searches</h2>
        <button type="button" disabled={disabled} onClick={onSave}>
          Save current search
        </button>
      </div>
      {saved.length === 0 ? (
        <p data-testid="saved-empty" className="saved-empty">
          Saved searches appear here so you can return without retyping. They
          stay in this browser.
        </p>
      ) : (
        <ul className="saved-list">
          {saved.map((s) => (
            <li
              key={s.id}
              data-testid="saved-item"
              className={s.id === activeId ? 'saved-item saved-item--active' : 'saved-item'}
            >
              <button
                type="button"
                className="saved-item__run"
                disabled={disabled}
                onClick={() => onRun(s)}
              >
                {s.query}
              </button>
              <button
                type="button"
                className="saved-item__remove"
                aria-label={`Remove ${s.query}`}
                disabled={disabled}
                onClick={() => onRemove(s.id)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
