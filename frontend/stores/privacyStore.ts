import { create } from "zustand";

import * as privacyApi from "@/services/privacy";
import * as moderationApi from "@/services/moderation";
import type { BlockedUser, PrivacySettings } from "@/types/moderation";

type PrivacyState = {
  settings: PrivacySettings | null;
  blockedUsers: BlockedUser[];
  loading: boolean;
  error: string | null;
  loadSettings: () => Promise<void>;
  updateSettings: (payload: Partial<PrivacySettings>) => Promise<void>;
  loadBlockedUsers: () => Promise<void>;
  blockUser: (username: string, reason?: string) => Promise<void>;
  unblockUser: (username: string) => Promise<void>;
  reset: () => void;
};

const initial = {
  settings: null as PrivacySettings | null,
  blockedUsers: [] as BlockedUser[],
  loading: false,
  error: null as string | null,
};

export const usePrivacyStore = create<PrivacyState>((set, get) => ({
  ...initial,

  loadSettings: async () => {
    set({ loading: true, error: null });
    try {
      const settings = await privacyApi.getPrivacySettings();
      set({ settings, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load privacy settings",
      });
      throw err;
    }
  },

  updateSettings: async (payload) => {
    const settings = await privacyApi.updatePrivacySettings(payload);
    set({ settings });
  },

  loadBlockedUsers: async () => {
    set({ loading: true, error: null });
    try {
      const blockedUsers = await moderationApi.getBlockedUsers();
      set({ blockedUsers, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load blocked users",
      });
      throw err;
    }
  },

  blockUser: async (username, reason = "") => {
    await moderationApi.blockUser(username, reason);
    await get().loadBlockedUsers();
  },

  unblockUser: async (username) => {
    await moderationApi.unblockUser(username);
    set({
      blockedUsers: get().blockedUsers.filter((u) => u.username !== username),
    });
  },

  reset: () => set(initial),
}));
