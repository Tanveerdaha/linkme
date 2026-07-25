import api from "@/services/api";
import type {
  AdminComment,
  AdminMe,
  AdminPost,
  AdminReport,
  AdminUser,
  AdminUserDetail,
  AnalyticsMetrics,
  AnalyticsTrends,
  AuditLogItem,
  DashboardOverview,
  ModerationHistoryItem,
  Paginated,
} from "@/types/admin";

export async function getAdminMe(): Promise<AdminMe> {
  const { data } = await api.get<AdminMe>("/admin/me/");
  return data;
}

export async function getDashboardStats(): Promise<DashboardOverview> {
  const { data } = await api.get<DashboardOverview>("/admin/analytics/overview/");
  return data;
}

export async function getAnalyticsTrends(days = 14): Promise<AnalyticsTrends> {
  const { data } = await api.get<AnalyticsTrends>("/admin/analytics/trends/", {
    params: { days },
  });
  return data;
}

export async function getAnalyticsMetrics(): Promise<AnalyticsMetrics> {
  const { data } = await api.get<AnalyticsMetrics>("/admin/analytics/metrics/");
  return data;
}

export async function getUsers(
  params?: Record<string, string | number | undefined>,
): Promise<Paginated<AdminUser>> {
  const { data } = await api.get<Paginated<AdminUser>>("/admin/users/", { params });
  return data;
}

export async function getUserDetail(id: string): Promise<AdminUserDetail> {
  const { data } = await api.get<AdminUserDetail>(`/admin/users/${id}/`);
  return data;
}

export async function suspendUser(
  id: string,
  payload: { reason?: string; duration?: string },
): Promise<{ suspended: boolean }> {
  const { data } = await api.post(`/admin/users/${id}/suspend/`, payload);
  return data;
}

export async function unsuspendUser(id: string): Promise<{ suspended: boolean }> {
  const { data } = await api.post(`/admin/users/${id}/unsuspend/`);
  return data;
}

export async function deactivateUser(
  id: string,
  reason = "",
): Promise<{ deactivated: boolean }> {
  const { data } = await api.post(`/admin/users/${id}/deactivate/`, { reason });
  return data;
}

export async function deleteUser(id: string, reason = ""): Promise<{ deleted: boolean }> {
  const { data } = await api.post(`/admin/users/${id}/delete/`, { reason });
  return data;
}

export async function getPosts(
  params?: Record<string, string | undefined>,
): Promise<Paginated<AdminPost>> {
  const { data } = await api.get<Paginated<AdminPost>>("/admin/content/posts/", {
    params,
  });
  return data;
}

export async function removePost(id: string, reason = ""): Promise<void> {
  await api.delete(`/admin/content/posts/${id}/`, { data: { reason } });
}

export async function restorePost(id: string): Promise<void> {
  await api.post(`/admin/content/posts/${id}/restore/`);
}

export async function getComments(
  params?: Record<string, string | undefined>,
): Promise<Paginated<AdminComment>> {
  const { data } = await api.get<Paginated<AdminComment>>("/admin/content/comments/", {
    params,
  });
  return data;
}

export async function removeComment(id: string, reason = ""): Promise<void> {
  await api.delete(`/admin/content/comments/${id}/`, { data: { reason } });
}

export async function restoreComment(id: string): Promise<void> {
  await api.post(`/admin/content/comments/${id}/restore/`);
}

export async function getReports(
  params?: Record<string, string | undefined>,
): Promise<Paginated<AdminReport>> {
  const { data } = await api.get<Paginated<AdminReport>>("/admin/reports/", { params });
  return data;
}

export async function getReport(id: string): Promise<AdminReport> {
  const { data } = await api.get<AdminReport>(`/admin/reports/${id}/`);
  return data;
}

export async function updateReport(
  id: string,
  payload: { status: string; note?: string },
): Promise<AdminReport> {
  const { data } = await api.patch<AdminReport>(`/admin/reports/${id}/`, payload);
  return data;
}

export async function getModerationHistory(
  params?: Record<string, string | undefined>,
): Promise<Paginated<ModerationHistoryItem>> {
  const { data } = await api.get<Paginated<ModerationHistoryItem>>(
    "/admin/moderation/history/",
    { params },
  );
  return data;
}

export async function getAuditLogs(
  params?: Record<string, string | undefined>,
): Promise<Paginated<AuditLogItem>> {
  const { data } = await api.get<Paginated<AuditLogItem>>("/admin/audit/", { params });
  return data;
}

export async function requestExport(payload: {
  export_type: string;
  format?: string;
  filters?: Record<string, unknown>;
}): Promise<{ id: string; status: string }> {
  const { data } = await api.post("/admin/export/", payload);
  return data;
}
