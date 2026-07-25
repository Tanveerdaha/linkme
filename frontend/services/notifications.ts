import api from "@/services/api";
import type { PageResult } from "@/types";
import type {
  AppNotification,
  NotificationPreferences,
  UnreadCount,
} from "@/types/notifications";

export async function getNotifications(params?: {
  page?: number;
  unread?: boolean;
}): Promise<PageResult<AppNotification>> {
  const { data } = await api.get<PageResult<AppNotification>>("/notifications/", {
    params: {
      page: params?.page,
      unread: params?.unread ? "true" : undefined,
    },
  });
  return data;
}

export async function getUnreadCount(): Promise<UnreadCount> {
  const { data } = await api.get<UnreadCount>("/notifications/unread-count/");
  return data;
}

export async function markNotificationRead(
  id: string,
): Promise<AppNotification> {
  const { data } = await api.patch<AppNotification>(
    `/notifications/${id}/read/`,
  );
  return data;
}

export async function markAllRead(): Promise<UnreadCount> {
  const { data } = await api.post<UnreadCount>("/notifications/read-all/");
  return data;
}

export async function deleteNotification(id: string): Promise<void> {
  await api.delete(`/notifications/${id}/`);
}

export async function getPreferences(): Promise<NotificationPreferences> {
  const { data } = await api.get<NotificationPreferences>(
    "/notifications/preferences/",
  );
  return data;
}

export async function updatePreferences(
  payload: Partial<NotificationPreferences>,
): Promise<NotificationPreferences> {
  const { data } = await api.patch<NotificationPreferences>(
    "/notifications/preferences/",
    payload,
  );
  return data;
}

/** Build frontend href for a notification target. */
export function notificationHref(notification: AppNotification): string | null {
  const type = notification.type || notification.notification_type || "";
  const objectType = notification.object_type;
  const objectId = notification.object_id;

  if (type === "CONNECTION_REQUEST" || type === "CONNECTION_ACCEPTED") {
    const username =
      objectType === "user" ? objectId : notification.sender?.username;
    return username ? `/u/${username}` : "/network/requests";
  }

  if (type === "MESSAGE_RECEIVED" || objectType === "conversation") {
    return objectId ? `/messages/${objectId}` : "/messages";
  }

  if (objectType === "post" || type.startsWith("POST_") || type.startsWith("COMMENT_")) {
    const [postId, commentId] = objectId.split("|");
    if (!postId) return null;
    return commentId ? `/post/${postId}?comment=${commentId}` : `/post/${postId}`;
  }

  return null;
}
