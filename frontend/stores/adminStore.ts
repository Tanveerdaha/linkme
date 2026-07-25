import { create } from "zustand";

import * as adminApi from "@/services/admin";
import type {
  AdminComment,
  AdminMe,
  AdminPermission,
  AdminPost,
  AdminReport,
  AdminUser,
  AnalyticsMetrics,
  AnalyticsTrends,
  AuditLogItem,
  DashboardOverview,
  ModerationHistoryItem,
} from "@/types/admin";

type AdminFilters = Record<string, string>;

type AdminState = {
  me: AdminMe | null;
  overview: DashboardOverview | null;
  trends: AnalyticsTrends | null;
  metrics: AnalyticsMetrics | null;
  users: AdminUser[];
  usersCount: number;
  reports: AdminReport[];
  reportsCount: number;
  posts: AdminPost[];
  comments: AdminComment[];
  moderation: ModerationHistoryItem[];
  auditLogs: AuditLogItem[];
  filters: AdminFilters;
  loading: boolean;
  error: string | null;
  hasPermission: (code: AdminPermission) => boolean;
  setFilter: (key: string, value: string) => void;
  clearFilters: () => void;
  loadMe: () => Promise<AdminMe>;
  loadOverview: () => Promise<void>;
  loadAnalytics: () => Promise<void>;
  loadUsers: (params?: AdminFilters) => Promise<void>;
  loadReports: (params?: AdminFilters) => Promise<void>;
  loadPosts: (params?: AdminFilters) => Promise<void>;
  loadComments: (params?: AdminFilters) => Promise<void>;
  loadModeration: () => Promise<void>;
  loadAudit: (params?: AdminFilters) => Promise<void>;
  reset: () => void;
};

const initial = {
  me: null as AdminMe | null,
  overview: null as DashboardOverview | null,
  trends: null as AnalyticsTrends | null,
  metrics: null as AnalyticsMetrics | null,
  users: [] as AdminUser[],
  usersCount: 0,
  reports: [] as AdminReport[],
  reportsCount: 0,
  posts: [] as AdminPost[],
  comments: [] as AdminComment[],
  moderation: [] as ModerationHistoryItem[],
  auditLogs: [] as AuditLogItem[],
  filters: {} as AdminFilters,
  loading: false,
  error: null as string | null,
};

export const useAdminStore = create<AdminState>((set, get) => ({
  ...initial,

  hasPermission: (code) => {
    const me = get().me;
    if (!me) return false;
    if (me.is_superuser || me.role === "SUPER_ADMIN") return true;
    return me.permissions.includes(code);
  },

  setFilter: (key, value) =>
    set({ filters: { ...get().filters, [key]: value } }),

  clearFilters: () => set({ filters: {} }),

  loadMe: async () => {
    const me = await adminApi.getAdminMe();
    set({ me });
    return me;
  },

  loadOverview: async () => {
    set({ loading: true, error: null });
    try {
      const overview = await adminApi.getDashboardStats();
      set({ overview, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load overview",
      });
      throw err;
    }
  },

  loadAnalytics: async () => {
    set({ loading: true, error: null });
    try {
      const [trends, metrics] = await Promise.all([
        adminApi.getAnalyticsTrends(14),
        adminApi.getAnalyticsMetrics(),
      ]);
      set({ trends, metrics, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load analytics",
      });
      throw err;
    }
  },

  loadUsers: async (params) => {
    set({ loading: true, error: null });
    try {
      const page = await adminApi.getUsers({ ...get().filters, ...params });
      set({ users: page.results, usersCount: page.count, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load users",
      });
      throw err;
    }
  },

  loadReports: async (params) => {
    set({ loading: true, error: null });
    try {
      const page = await adminApi.getReports({ ...get().filters, ...params });
      set({ reports: page.results, reportsCount: page.count, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load reports",
      });
      throw err;
    }
  },

  loadPosts: async (params) => {
    set({ loading: true });
    const page = await adminApi.getPosts(params);
    set({ posts: page.results, loading: false });
  },

  loadComments: async (params) => {
    set({ loading: true });
    const page = await adminApi.getComments(params);
    set({ comments: page.results, loading: false });
  },

  loadModeration: async () => {
    set({ loading: true });
    const page = await adminApi.getModerationHistory();
    set({ moderation: page.results, loading: false });
  },

  loadAudit: async (params) => {
    set({ loading: true });
    const page = await adminApi.getAuditLogs({ ...get().filters, ...params });
    set({ auditLogs: page.results, loading: false });
  },

  reset: () => set(initial),
}));
