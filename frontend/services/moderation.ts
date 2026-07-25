import api from "@/services/api";
import type {
  BlockedUser,
  ModerationActionType,
  Report,
  ReportContentType,
  ReportReason,
  ReportStatus,
} from "@/types/moderation";

export async function blockUser(username: string, reason = ""): Promise<{ blocked: boolean }> {
  const { data } = await api.post<{ blocked: boolean }>(`/users/${username}/block/`, {
    reason,
  });
  return data;
}

export async function unblockUser(username: string): Promise<void> {
  await api.delete(`/users/${username}/block/`);
}

export async function getBlockedUsers(): Promise<BlockedUser[]> {
  const { data } = await api.get<{ results: BlockedUser[] }>("/users/blocked/");
  return data.results;
}

export async function createReport(payload: {
  content_type: ReportContentType;
  object_id: string;
  reason: ReportReason;
  description?: string;
}): Promise<Report> {
  const { data } = await api.post<Report>("/reports/", payload);
  return data;
}

export async function getMyReports(): Promise<Report[]> {
  const { data } = await api.get<{ results: Report[] }>("/reports/my/");
  return data.results;
}

export async function getAdminReports(status?: ReportStatus): Promise<Report[]> {
  const { data } = await api.get<{ results: Report[] }>("/reports/admin/reports/", {
    params: status ? { status } : undefined,
  });
  return data.results;
}

export async function getAdminReport(reportId: string): Promise<Report> {
  const { data } = await api.get<Report>(`/reports/admin/reports/${reportId}/`);
  return data;
}

export async function updateReportStatus(
  reportId: string,
  status: ReportStatus,
): Promise<Report> {
  const { data } = await api.patch<Report>(`/reports/admin/reports/${reportId}/`, {
    status,
  });
  return data;
}

export async function takeModerationAction(payload: {
  target_type: string;
  target_id: string;
  action: ModerationActionType;
  reason?: string;
  report_id?: string;
  suspend_days?: number;
}): Promise<unknown> {
  const { data } = await api.post("/reports/admin/actions/", payload);
  return data;
}
