"use client";

import { useCallback, useEffect, useState } from "react";

import { BottomNav } from "@/components/layout/bottom-nav";
import { SiteHeader } from "@/components/layout/site-header";
import { PeopleSuggestions } from "@/components/search/PeopleSuggestions";
import { RecentSearches } from "@/components/search/RecentSearches";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchEmptyState } from "@/components/search/SearchEmptyState";
import { SearchResults } from "@/components/search/SearchResults";
import { getApiErrorMessage } from "@/services/api";
import { useSearchStore } from "@/stores/searchStore";

export default function UserSearchPage() {
  const query = useSearchStore((s) => s.query);
  const results = useSearchStore((s) => s.results);
  const resultCount = useSearchStore((s) => s.resultCount);
  const page = useSearchStore((s) => s.page);
  const loading = useSearchStore((s) => s.loading);
  const setQuery = useSearchStore((s) => s.setQuery);
  const setPage = useSearchStore((s) => s.setPage);
  const searchUsers = useSearchStore((s) => s.searchUsers);
  const clearResults = useSearchStore((s) => s.clearResults);
  const loadSuggestions = useSearchStore((s) => s.loadSuggestions);

  const [error, setError] = useState<string | null>(null);
  const isSearching = Boolean(query.trim());

  useEffect(() => {
    void loadSuggestions();
  }, [loadSuggestions]);

  useEffect(() => {
    if (!isSearching) {
      clearResults();
      setError(null);
      return;
    }
    let cancelled = false;
    void searchUsers({ q: query, page })
      .then(() => {
        if (!cancelled) setError(null);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(getApiErrorMessage(err, "Search failed"));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [query, page, isSearching, searchUsers, clearResults]);

  const handleSearch = useCallback(
    (q: string) => {
      setQuery(q);
    },
    [setQuery],
  );

  const handleSelectRecent = useCallback(
    (term: string) => {
      setQuery(term);
    },
    [setQuery],
  );

  const handlePageChange = useCallback(
    (nextPage: number) => {
      setPage(nextPage);
    },
    [setPage],
  );

  return (
    <div className="min-h-screen pb-16 md:pb-0">
      <SiteHeader />
      <main className="mx-auto w-full max-w-[800px] px-4 py-8 sm:py-10">
        <div className="space-y-6">
          <div>
            <h1 className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight">
              Find people
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Search by name, username, headline, or location.
            </p>
          </div>

          <SearchBar
            value={query}
            onSearch={handleSearch}
            autoFocus
            placeholder="Search people…"
          />

          {error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : null}

          {isSearching ? (
            <SearchResults
              results={results}
              loading={loading}
              count={resultCount}
              page={page}
              pageSize={20}
              onPageChange={handlePageChange}
              emptyMessage={
                loading
                  ? "Searching…"
                  : "No people found. Try another name or location."
              }
            />
          ) : (
            <>
              <PeopleSuggestions limit={4} />
              <RecentSearches onSelect={handleSelectRecent} />
              <SearchEmptyState />
            </>
          )}
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
