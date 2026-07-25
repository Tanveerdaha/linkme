import { create } from "zustand";
import { persist } from "zustand/middleware";

import * as authApi from "@/services/auth";
import type { AuthUser } from "@/types";

const ACCESS_KEY = "linkme_access_token";
const REFRESH_KEY = "linkme_refresh_token";

type AuthState = {
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  _hasHydrated: boolean;
  setHasHydrated: (value: boolean) => void;
  setSession: (access: string, refresh: string, user: AuthUser) => void;
  login: (login: string, password: string) => Promise<void>;
  loginWithGoogle: (payload: { code?: string; token?: string }) => Promise<void>;
  loginWithPhone: (phone_number: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<string | null>;
  clearAuth: () => void;
};

function syncTokenStorage(access: string | null, refresh: string | null) {
  if (typeof window === "undefined") return;
  if (access) {
    window.localStorage.setItem(ACCESS_KEY, access);
  } else {
    window.localStorage.removeItem(ACCESS_KEY);
  }
  if (refresh) {
    window.localStorage.setItem(REFRESH_KEY, refresh);
  } else {
    window.localStorage.removeItem(REFRESH_KEY);
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      _hasHydrated: false,
      setHasHydrated: (value) => set({ _hasHydrated: value }),
      setSession: (access, refresh, user) => {
        syncTokenStorage(access, refresh);
        set({
          accessToken: access,
          refreshToken: refresh,
          user,
          isAuthenticated: true,
        });
      },
      login: async (login, password) => {
        const data = await authApi.login({ login, password });
        get().setSession(data.access, data.refresh, data.user);
      },
      loginWithGoogle: async (payload) => {
        const data = await authApi.loginWithGoogle(payload);
        get().setSession(data.access, data.refresh, data.user);
      },
      loginWithPhone: async (phone_number, code) => {
        const data = await authApi.verifyPhoneOtp(phone_number, code);
        get().setSession(data.access, data.refresh, data.user);
      },
      logout: async () => {
        const refresh = get().refreshToken;
        try {
          if (refresh) {
            await authApi.logout(refresh);
          }
        } catch {
          // Clear local session even if blacklist call fails.
        } finally {
          get().clearAuth();
        }
      },
      refreshSession: async () => {
        const refresh = get().refreshToken;
        if (!refresh) {
          get().clearAuth();
          return null;
        }
        try {
          const data = await authApi.refreshToken(refresh);
          const nextRefresh = data.refresh ?? refresh;
          syncTokenStorage(data.access, nextRefresh);
          set({
            accessToken: data.access,
            refreshToken: nextRefresh,
            isAuthenticated: true,
          });
          return data.access;
        } catch {
          get().clearAuth();
          return null;
        }
      },
      clearAuth: () => {
        syncTokenStorage(null, null);
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: "linkme-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) {
          syncTokenStorage(state.accessToken, state.refreshToken);
        }
        state?.setHasHydrated(true);
      },
    },
  ),
);
