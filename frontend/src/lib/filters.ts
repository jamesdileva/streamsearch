export interface FilterState {
  platform: string;
  sort: string;
  hasLocation: boolean;
}

export const DEFAULT_FILTERS: FilterState = {
  platform: 'all',
  sort: 'relevance',
  hasLocation: false,
};
