"use client";

import { NotificationItem } from "@/components/notifications/NotificationItem";
import { Loader } from "@/components/ui/loader";
import type { AppNotification } from "@/types/notifications";

type NotificationListProps = {
  notifications: AppNotification[];
  loading?: boolean;
  onItemClick?: (notification: AppNotification) => void;
  emptyMessage?: string;
};

export function NotificationList({
  notifications,
  loading,
  onItemClick,
  emptyMessage = "No notifications yet.",
}: NotificationListProps) {
  if (loading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader />
      </div>
    );
  }

  if (!notifications.length) {
    return (
      <div className="px-6 py-10 text-center text-sm text-muted-foreground">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="divide-y divide-border/50">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClick={onItemClick}
        />
      ))}
    </div>
  );
}
