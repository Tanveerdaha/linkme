"use client";

import { Search } from "lucide-react";
import { useEffect, useState } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type SearchBarProps = {
  initialQuery?: string;
  value?: string;
  placeholder?: string;
  onSearch: (query: string) => void;
  className?: string;
  autoFocus?: boolean;
};

export function SearchBar({
  initialQuery = "",
  value,
  placeholder = "Search people…",
  onSearch,
  className,
  autoFocus,
}: SearchBarProps) {
  const [query, setQuery] = useState(value ?? initialQuery);

  useEffect(() => {
    if (value !== undefined && value !== query) {
      setQuery(value);
    }
    // Sync when parent sets query (e.g. recent search click).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      onSearch(query.trim());
    }, 300);
    return () => window.clearTimeout(handle);
    // Debounce query changes; parent should stabilize onSearch (useCallback).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  return (
    <div className={cn("relative", className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className="pl-9"
        aria-label="Search users"
      />
    </div>
  );
}
