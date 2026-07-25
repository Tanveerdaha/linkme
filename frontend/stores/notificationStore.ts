import { create } from "zustand";

import * as notificationsApi from "@/services/notifications";
import {
  connectNotificationSocket,
  disconnectNotificationSocket,
  sendNotificationEvent,
  subscribeNotifications,
} from "@/services/socket";
import { useAuthStore } from "@/stores/authStore";
import type {
  AppNotification,
  NotificationPreferences,
} from "@/types/notifications";

type NotificationState = {
  notifications: AppNotification[];
  unreadCount: number;
  loading: boolean;
  preferences: NotificationPreferences | null;
  connected: boolean;
  error: string | null;
  loadNotifications: (opts?: { unread?: boolean }) => Promise<void>;
  loadUnreadCount: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
  deleteNotification: (id: string) => Promise<void>;
  loadPreferences: () => Promise<void>;
  updatePreferences: (
    payload: Partial<NotificationPreferences>,
  ) => Promise<void>;
  receiveRealtimeNotification: (notification: AppNotification) => void;
  connectRealtime: () => void;
  disconnectRealtime: () => void;
  reset: () => void;
};

const initial = {
  notifications: [] as AppNotification[],
  unreadCount: 0,
  loading: false,
  preferences: null as NotificationPreferences | null,
  connected: false,
  error: null as string | null,
};

let unsubscribers: Array<() => void> = [];

function clearSubs() {
  unsubscribers.forEach((u) => u());
  unsubscribers = [];
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  ...initial,

  loadNotifications: async (opts) => {
    set({ loading: true, error: null });
    try {
      const page = await notificationsApi.getNotifications({
        unread: opts?.unread,
      });
      set({ notifications: page.results, loading: false });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load notifications",
      });
    }
  },

  loadUnreadCount: async () => {
    try {
      const data = await notificationsApi.getUnreadCount();
      set({ unreadCount: data.count });
    } catch {
      // ignore
    }
  },

  markRead: async (id) => {
    const updated = await notificationsApi.markNotificationRead(id);
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, ...updated, is_read: true } : n,
      ),
      unreadCount: Math.max(
        0,
        state.notifications.find((n) => n.id === id && !n.is_read)
          ? state.unreadCount - 1
          : state.unreadCount,
      ),
    }));
    sendNotificationEvent({ type: "notification.read", id });
  },

  markAllRead: async () => {
    await notificationsApi.markAllRead();
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, is_read: true })),
      unreadCount: 0,
    }));
    sendNotificationEvent({ type: "notification.read_all" });
  },

  deleteNotification: async (id) => {
    const existing = get().notifications.find((n) => n.id === id);
    await notificationsApi.deleteNotification(id);
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
      unreadCount:
        existing && !existing.is_read
          ? Math.max(0, state.unreadCount - 1)
          : state.unreadCount,
    }));
  },

  loadPreferences: async () => {
    const preferences = await notificationsApi.getPreferences();
    set({ preferences });
  },

  updatePreferences: async (payload) => {
    const preferences = await notificationsApi.updatePreferences(payload);
    set({ preferences });
  },

  receiveRealtimeNotification: (notification) => {
    set((state) => {
      if (state.notifications.some((n) => n.id === notification.id)) {
        return state;
      }
      return {
        notifications: [notification, ...state.notifications],
        unreadCount: notification.is_read
          ? state.unreadCount
          : state.unreadCount + 1,
      };
    });
  },

  connectRealtime: () => {
    const token = useAuthStore.getState().accessToken;
    if (!token) return;

    clearSubs();
    disconnectNotificationSocket();
    connectNotificationSocket(token);

    unsubscribers = [
      subscribeNotifications("notification.new", (payload) => {
        const notification = payload.notification as AppNotification | undefined;
        if (notification) {
          get().receiveRealtimeNotification(notification);
        }
      }),
      subscribeNotifications("notification.unread_count", (payload) => {
        set({ unreadCount: Number(payload.count || 0), connected: true });
      }),
      subscribeNotifications("socket.open", () => {
        set({ connected: true });
      }),
      subscribeNotifications("socket.close", () => {
        set({ connected: false });
      }),
    ];
  },

  disconnectRealtime: () => {
    clearSubs();
    disconnectNotificationSocket();
    set({ connected: false });
  },

  reset: () => {
    clearSubs();
    disconnectNotificationSocket();
    set({ ...initial });
  },
}));
