"use client";

import { useEffect, useState } from "react";

import { BottomNav } from "@/components/layout/bottom-nav";
import { NotificationList } from "@/components/notifications/NotificationList";
import { NotificationSettings } from "@/components/notifications/NotificationSettings";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useNotificationStore } from "@/stores/notificationStore";
import type { AppNotification } from "@/types/notifications";

type Tab = "all" | "unread" | "settings";

export default function NotificationsPage() {
  const [tab, setTab] = useState<Tab>("all");
  const notifications = useNotificationStore((s) => s.notifications);
  const loading = useNotificationStore((s) => s.loading);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const loadNotifications = useNotificationStore((s) => s.loadNotifications);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);

  useEffect(() => {
    if (tab === "settings") return;
    void loadNotifications({ unread: tab === "unread" });
  }, [tab, loadNotifications]);

  const onItemClick = (notification: AppNotification) => {
    if (!notification.is_read) {
      void markRead(notification.id);
    }
  };

  return (
    <>
      <main className="mx-auto w-full max-w-2xl px-4 py-8 pb-20 md:pb-10">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight">
              Notifications
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Stay on top of reactions, comments, connections, and messages.
            </p>
          </div>
          {unreadCount > 0 && tab !== "settings" ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void markAllRead()}
            >
              Mark all read
            </Button>
          ) : null}
        </div>

        <div className="mb-4 flex gap-1 rounded-xl border border-border/60 bg-card/60 p-1">
          {(
            [
              ["all", "All"],
              ["unread", "Unread"],
              ["settings", "Settings"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={cn(
                "flex-1 rounded-lg px-3 py-2 text-sm transition-colors",
                tab === key
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {label}
              {key === "unread" && unreadCount > 0 ? (
                <span className="ml-1 text-xs opacity-80">({unreadCount})</span>
              ) : null}
            </button>
          ))}
        </div>

        <section className="overflow-hidden rounded-2xl border border-border/70 bg-card/80">
          {tab === "settings" ? (
            <div className="p-4">
              <NotificationSettings />
            </div>
          ) : (
            <NotificationList
              notifications={notifications}
              loading={loading}
              onItemClick={onItemClick}
              emptyMessage={
                tab === "unread"
                  ? "You're all caught up."
                  : "No notifications yet."
              }
            />
          )}
        </section>
      </main>
      <BottomNav />
    </>
  );
}
