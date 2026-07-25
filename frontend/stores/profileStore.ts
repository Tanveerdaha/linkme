import { create } from "zustand";

import * as profileApi from "@/services/profile";
import * as searchApi from "@/services/search";
import type {
  MeProfile,
  PublicProfile,
  SuggestedUser,
  UserSearchResult,
} from "@/types";

type ProfileState = {
  currentProfile: MeProfile | PublicProfile | null;
  loading: boolean;
  searchResults: UserSearchResult[];
  searchCount: number;
  searchPage: number;
  searchLoading: boolean;
  suggestions: SuggestedUser[];
  setCurrentProfile: (profile: MeProfile | PublicProfile | null) => void;
  updateProfile: (formData: FormData) => Promise<MeProfile>;
  searchUsers: (params: {
    q?: string;
    location?: string;
    interest?: string;
    page?: number;
  }) => Promise<void>;
  loadSuggestions: () => Promise<void>;
  resetSearch: () => void;
};

export const useProfileStore = create<ProfileState>((set) => ({
  currentProfile: null,
  loading: false,
  searchResults: [],
  searchCount: 0,
  searchPage: 1,
  searchLoading: false,
  suggestions: [],
  setCurrentProfile: (profile) => set({ currentProfile: profile }),
  updateProfile: async (formData) => {
    const profile = await profileApi.updateMeProfile(formData);
    set({ currentProfile: profile });
    return profile;
  },
  searchUsers: async (params) => {
    set({ searchLoading: true });
    try {
      const page = await searchApi.searchUsers(params);
      set({
        searchResults: page.results,
        searchCount: page.count,
        searchPage: params.page || 1,
        searchLoading: false,
      });
    } catch (err) {
      set({ searchLoading: false, searchResults: [] });
      throw err;
    }
  },
  loadSuggestions: async () => {
    const suggestions = await profileApi.getSuggestions();
    set({ suggestions });
  },
  resetSearch: () =>
    set({ searchResults: [], searchCount: 0, searchPage: 1, searchLoading: false }),
}));
