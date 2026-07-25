import api from "@/services/api";
import type { PrivacySettings } from "@/types/moderation";

export async function getPrivacySettings(): Promise<PrivacySettings> {
  const { data } = await api.get<PrivacySettings>("/privacy/settings/");
  return data;
}

export async function updatePrivacySettings(
  payload: Partial<PrivacySettings>,
): Promise<PrivacySettings> {
  const { data } = await api.patch<PrivacySettings>("/privacy/settings/", payload);
  return data;
}
