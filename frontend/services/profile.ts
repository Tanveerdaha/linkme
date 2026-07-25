import api from "@/services/api";
import type {
  ActivityItem,
  MeProfile,
  ProfileMediaGallery,
  PublicProfile,
  SuggestedUser,
} from "@/types";

export async function getMeProfile(): Promise<MeProfile> {
  const { data } = await api.get<MeProfile>("/profile/me/");
  return data;
}

export async function updateMeProfile(formData: FormData): Promise<MeProfile> {
  const { data } = await api.patch<MeProfile>("/profile/me/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    transformRequest: [
      (body: unknown, headers?: Record<string, unknown>) => {
        if (headers && typeof headers === "object") {
          delete headers["Content-Type"];
        }
        return body;
      },
    ],
  });
  return data;
}

export async function getPublicProfile(username: string): Promise<PublicProfile> {
  const { data } = await api.get<PublicProfile>(`/profile/${username}/`);
  return data;
}

export async function getProfileMedia(username: string): Promise<ProfileMediaGallery> {
  const { data } = await api.get<ProfileMediaGallery>(`/profile/${username}/media/`);
  return data;
}

export async function getProfileActivity(username: string): Promise<ActivityItem[]> {
  const { data } = await api.get<ActivityItem[]>(`/profile/${username}/activity/`);
  return data;
}

export async function getSuggestions(): Promise<SuggestedUser[]> {
  const { data } = await api.get<SuggestedUser[]>("/users/suggestions/");
  return data;
}

/** @deprecated Prefer importing from services/profile — kept for auth.ts re-exports. */
export { getMeProfile as getProfile, updateMeProfile as updateProfile };
