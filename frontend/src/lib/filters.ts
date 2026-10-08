export interface FilterState {
  platform: string;
  sort: string;
  hasLocation: boolean;
  // Sprint 8.1. '' = no filter (backend treats absent as "any").
  language: string;
  minViewers: number;
}

export const DEFAULT_FILTERS: FilterState = {
  platform: 'all',
  sort: 'relevance',
  hasLocation: false,
  language: '',
  minViewers: 0,
};
