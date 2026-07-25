"use client";

import Link from "next/link";
import { useEffect } from "react";

import { NotificationList } from "@/components/notifications/NotificationList";
import { Button } from "@/components/ui/button";
import { useNotificationStore } from "@/stores/notificationStore";
import type { AppNotification } from "@/types/notifications";

type NotificationDropdownProps = {
  open: boolean;
  onClose: () => void;
};

export function NotificationDropdown({ open, onClose }: NotificationDropdownProps) {
  const notifications = useNotificationStore((s) => s.notifications);
  const loading = useNotificationStore((s) => s.loading);
  const loadNotifications = useNotificationStore((s) => s.loadNotifications);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const unreadCount = useNotificationStore((s) => s.unreadCount);

  useEffect(() => {
    if (open) {
      void loadNotifications();
    }
  }, [open, loadNotifications]);

  if (!open) return null;

  const handleClick = (notification: AppNotification) => {
    if (!notification.is_read) {
      void markRead(notification.id);
    }
    onClose();
  };

  return (
    <div className="absolute right-0 top-full z-50 mt-2 w-[min(100vw-2rem,22rem)] overflow-hidden rounded-xl border border-border/70 bg-card shadow-lg animate-fade-up">
      <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
        <p className="font-[family-name:var(--font-fraunces)] text-base font-semibold">
          Notifications
        </p>
        {unreadCount > 0 ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 text-xs"
            onClick={() => void markAllRead()}
          >
            Mark all read
          </Button>
        ) : null}
      </div>
      <div className="max-h-80 overflow-y-auto">
        <NotificationList
          notifications={notifications.slice(0, 8)}
          loading={loading}
          onItemClick={handleClick}
        />
      </div>
      <div className="border-t border-border/60 p-2">
        <Button asChild variant="ghost" className="w-full" onClick={onClose}>
          <Link href="/notifications">View all</Link>
        </Button>
      </div>
    </div>
  );
}
