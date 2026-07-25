import api from "@/services/api";
import type { AccountStatus, DataExportStatus } from "@/types/moderation";

export async function getAccountStatus(): Promise<AccountStatus> {
  const { data } = await api.get<AccountStatus>("/account/status/");
  return data;
}

export async function deleteAccount(): Promise<{ deleted: boolean; message: string }> {
  const { data } = await api.delete<{ deleted: boolean; message: string }>("/account/");
  return data;
}

export async function restoreAccount(): Promise<{ restored: boolean }> {
  const { data } = await api.post<{ restored: boolean }>("/account/restore/");
  return data;
}

export async function requestDataExport(): Promise<{
  id: string;
  status: string;
  message: string;
}> {
  const { data } = await api.post<{ id: string; status: string; message: string }>(
    "/account/export/",
  );
  return data;
}

export async function getDataExportStatus(): Promise<DataExportStatus> {
  const { data } = await api.get<DataExportStatus>("/account/export/");
  return data;
}
