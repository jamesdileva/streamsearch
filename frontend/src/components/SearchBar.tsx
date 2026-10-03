import { useState, type FormEvent } from 'react';

interface SearchBarProps {
  isLoading?: boolean;
  onSearch: (query: string) => void;
}

export default function SearchBar({
  isLoading = false,
  onSearch,
}: SearchBarProps) {
  const [value, setValue] = useState('');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    onSearch(value);
  };

  return (
    <form role="search" onSubmit={submit} className="search-bar">
      <label htmlFor="streamsearch-input" className="visually-hidden">
        Search live streams
      </label>
      <input
        id="streamsearch-input"
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="wildfire near Los Angeles"
        autoComplete="off"
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Searching…' : 'Search'}
      </button>
    </form>
  );
}
