import { create } from "zustand";
import { persist } from "zustand/middleware";

import { getSuggestions } from "@/services/profile";
import { searchUsers as searchUsersApi } from "@/services/search";
import type { SuggestedUser, UserSearchResult } from "@/types";

const RECENT_STORAGE_CAP = 50;

type SearchState = {
  query: string;
  recentSearches: string[];
  suggestions: SuggestedUser[];
  results: UserSearchResult[];
  resultCount: number;
  page: number;
  loading: boolean;
  suggestionsLoading: boolean;
  setQuery: (query: string) => void;
  setPage: (page: number) => void;
  addRecentSearch: (term: string) => void;
  removeRecentSearch: (term: string) => void;
  clearRecentSearches: () => void;
  loadSuggestions: () => Promise<void>;
  searchUsers: (params?: { q?: string; page?: number }) => Promise<void>;
  clearResults: () => void;
};

export const useSearchStore = create<SearchState>()(
  persist(
    (set, get) => ({
      query: "",
      recentSearches: [],
      suggestions: [],
      results: [],
      resultCount: 0,
      page: 1,
      loading: false,
      suggestionsLoading: false,

      setQuery: (query) => set({ query, page: 1 }),

      setPage: (page) => set({ page }),

      addRecentSearch: (term) => {
        const normalized = term.trim();
        if (!normalized) return;
        const existing = get().recentSearches.filter(
          (item) => item.toLowerCase() !== normalized.toLowerCase(),
        );
        set({
          recentSearches: [normalized, ...existing].slice(0, RECENT_STORAGE_CAP),
        });
      },

      removeRecentSearch: (term) => {
        set({
          recentSearches: get().recentSearches.filter(
            (item) => item.toLowerCase() !== term.toLowerCase(),
          ),
        });
      },

      clearRecentSearches: () => set({ recentSearches: [] }),

      loadSuggestions: async () => {
        set({ suggestionsLoading: true });
        try {
          const suggestions = await getSuggestions();
          set({ suggestions, suggestionsLoading: false });
        } catch {
          set({ suggestionsLoading: false });
        }
      },

      searchUsers: async (params = {}) => {
        const q = (params.q ?? get().query).trim();
        const page = params.page ?? get().page;
        if (!q) {
          set({ results: [], resultCount: 0, loading: false, page: 1 });
          return;
        }
        set({ loading: true });
        try {
          const data = await searchUsersApi({ q, page, page_size: 20 });
          set({
            results: data.results,
            resultCount: data.count,
            page,
            loading: false,
          });
          get().addRecentSearch(q);
        } catch (err) {
          set({ loading: false, results: [], resultCount: 0 });
          throw err;
        }
      },

      clearResults: () =>
        set({ results: [], resultCount: 0, page: 1, loading: false }),
    }),
    {
      name: "linkme-search",
      partialize: (state) => ({ recentSearches: state.recentSearches }),
    },
  ),
);
