import { beforeEach, describe, expect, test } from 'vitest';
import {
  load,
  parse,
  remove,
  save,
} from './saved-searches';
import { DEFAULT_FILTERS } from './filters';

function memStorage(): Storage {
  const map = new Map<string, string>();
  return {
    get length() {
      return map.size;
    },
    clear: () => map.clear(),
    getItem: (k: string) => map.get(k) ?? null,
    key: (i: number) => [...map.keys()][i] ?? null,
    removeItem: (k: string) => void map.delete(k),
    setItem: (k: string, v: string) => void map.set(k, v),
  } as Storage;
}

let store: Storage;

beforeEach(() => {
  store = memStorage();
});

describe('parse', () => {
  test('returns [] for junk input', () => {
    expect(parse(null)).toEqual([]);
    expect(parse('not json')).toEqual([]);
    expect(parse('{"a":1}')).toEqual([]);
  });

  test('drops malformed entries and keeps valid ones', () => {
    const raw = JSON.stringify([
      { id: 'a', query: 'q', filters: DEFAULT_FILTERS, createdAt: 'now' },
      { id: 'b', query: 'q2' },
      'garbage',
    ]);
    const parsed = parse(raw);
    expect(parsed).toHaveLength(1);
    expect(parsed[0].id).toBe('a');
  });

  test('caps at 25 entries', () => {
    const raw = JSON.stringify(
      Array.from({ length: 30 }, (_, i) => ({
        id: `id-${i}`,
        query: `q${i}`,
        filters: DEFAULT_FILTERS,
        createdAt: 'now',
      })),
    );
    expect(parse(raw)).toHaveLength(25);
  });
});

describe('save / load', () => {
  test('round-trips through storage', () => {
    save('wildfire near LA', DEFAULT_FILTERS, store);
    const loaded = load(store);
    expect(loaded).toHaveLength(1);
    expect(loaded[0].query).toBe('wildfire near LA');
    expect(loaded[0].filters).toEqual(DEFAULT_FILTERS);
  });

  test('rejects empty queries', () => {
    expect(save('   ', DEFAULT_FILTERS, store)).toBeNull();
    expect(load(store)).toEqual([]);
  });

  test('ignores exact duplicates', () => {
    save('storm', DEFAULT_FILTERS, store);
    save('storm', DEFAULT_FILTERS, store);
    expect(load(store)).toHaveLength(1);
  });

  test('same query with different filters is saved separately', () => {
    save('storm', DEFAULT_FILTERS, store);
    save('storm', { ...DEFAULT_FILTERS, sort: 'viewers' }, store);
    expect(load(store)).toHaveLength(2);
  });

  test('newest first', () => {
    save('first', DEFAULT_FILTERS, store);
    save('second', DEFAULT_FILTERS, store);
    expect(load(store).map((s) => s.query)).toEqual(['second', 'first']);
  });
});

describe('remove', () => {
  test('removes only the given id', () => {
    save('one', DEFAULT_FILTERS, store);
    save('two', DEFAULT_FILTERS, store);
    const [first] = load(store);
    const rest = remove(first.id, store);
    expect(rest.map((s) => s.query)).toEqual(['one']);
  });
});
