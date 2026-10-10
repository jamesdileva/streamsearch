import type { FilterState } from './filters';

export interface SavedSearch {
  id: string;
  query: string;
  filters: FilterState;
  createdAt: string;
}

const STORAGE_KEY = 'streamsearch:saved-searches';
const MAX_SAVED = 25;

function isFilterState(value: unknown): value is FilterState {
  if (typeof value !== 'object' || value === null) return false;
  const f = value as Record<string, unknown>;
  return (
    typeof f.platform === 'string' &&
    typeof f.sort === 'string' &&
    typeof f.hasLocation === 'boolean' &&
    typeof f.language === 'string' &&
    typeof f.minViewers === 'number'
  );
}

export function parse(raw: string | null): SavedSearch[] {
  if (!raw) return [];
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return []; // corrupt entry: fail soft rather than break the UI
  }
  if (!Array.isArray(data)) return [];
  const out: SavedSearch[] = [];
  for (const item of data) {
    if (typeof item !== 'object' || item === null) continue;
    const s = item as Record<string, unknown>;
    if (
      typeof s.id === 'string' &&
      typeof s.query === 'string' &&
      typeof s.createdAt === 'string' &&
      isFilterState(s.filters)
    ) {
      out.push({
        id: s.id,
        query: s.query,
        filters: s.filters,
        createdAt: s.createdAt,
      });
    }
  }
  return out.slice(0, MAX_SAVED);
}

function newId(): string {
  return `ss-${Math.random().toString(36).slice(2, 10)}`;
}

function safeStorage(): Storage | undefined {
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

function persist(
  saved: SavedSearch[],
  storage: Storage | undefined,
): SavedSearch[] {
  const next = saved.slice(0, MAX_SAVED);
  try {
    storage?.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // quota / private mode: the in-memory list still works this session
  }
  return next;
}

export function load(storage: Storage | undefined = safeStorage()): SavedSearch[] {
  if (!storage) return [];
  return parse(storage.getItem(STORAGE_KEY));
}

/** Re-save an existing entry, or add it to the front. Returns null for an
 * empty query and the unchanged list when already saved. */
export function save(
  query: string,
  filters: FilterState,
  storage: Storage | undefined = safeStorage(),
): SavedSearch[] | null {
  const q = query.trim();
  if (!q) return null;
  const existing = load(storage);
  if (existing.some((s) => s.query === q && sameFilters(s.filters, filters))) {
    return existing;
  }
  const entry: SavedSearch = {
    id: newId(),
    query: q,
    filters,
    createdAt: new Date().toISOString(),
  };
  return persist([entry, ...existing], storage);
}

export function remove(
  id: string,
  storage: Storage | undefined = safeStorage(),
): SavedSearch[] {
  return persist(
    load(storage).filter((s) => s.id !== id),
    storage,
  );
}

function sameFilters(a: FilterState, b: FilterState): boolean {
  return (
    a.platform === b.platform &&
    a.sort === b.sort &&
    a.language === b.language &&
    a.minViewers === b.minViewers &&
    a.hasLocation === b.hasLocation
  );
}
