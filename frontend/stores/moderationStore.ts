import { create } from "zustand";

import * as moderationApi from "@/services/moderation";
import type { ModerationActionType, Report, ReportStatus } from "@/types/moderation";

type ModerationState = {
  reports: Report[];
  selectedReport: Report | null;
  loading: boolean;
  error: string | null;
  loadReports: (status?: ReportStatus) => Promise<void>;
  selectReport: (report: Report | null) => void;
  updateStatus: (reportId: string, status: ReportStatus) => Promise<void>;
  takeAction: (payload: {
    target_type: string;
    target_id: string;
    action: ModerationActionType;
    reason?: string;
    report_id?: string;
    suspend_days?: number;
  }) => Promise<void>;
  reset: () => void;
};

const initial = {
  reports: [] as Report[],
  selectedReport: null as Report | null,
  loading: false,
  error: null as string | null,
};

export const useModerationStore = create<ModerationState>((set, get) => ({
  ...initial,

  loadReports: async (status) => {
    set({ loading: true, error: null });
    try {
      const reports = await moderationApi.getAdminReports(status);
      set({ reports, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load reports",
      });
      throw err;
    }
  },

  selectReport: (report) => set({ selectedReport: report }),

  updateStatus: async (reportId, status) => {
    const updated = await moderationApi.updateReportStatus(reportId, status);
    set({
      reports: get().reports.map((r) => (r.id === reportId ? updated : r)),
      selectedReport:
        get().selectedReport?.id === reportId ? updated : get().selectedReport,
    });
  },

  takeAction: async (payload) => {
    await moderationApi.takeModerationAction(payload);
    if (payload.report_id) {
      await get().loadReports();
    }
  },

  reset: () => set(initial),
}));
