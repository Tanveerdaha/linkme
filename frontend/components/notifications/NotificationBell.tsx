"use client";

import { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";

import { NotificationDropdown } from "@/components/notifications/NotificationDropdown";
import { UnreadBadge } from "@/components/notifications/UnreadBadge";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";
import { useNotificationStore } from "@/stores/notificationStore";

export function NotificationBell() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const unreadCount = useNotificationStore((s) => s.unreadCount);
  const connectRealtime = useNotificationStore((s) => s.connectRealtime);
  const disconnectRealtime = useNotificationStore((s) => s.disconnectRealtime);
  const loadUnreadCount = useNotificationStore((s) => s.loadUnreadCount);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hasHydrated || !isAuthenticated) {
      disconnectRealtime();
      return;
    }
    connectRealtime();
    void loadUnreadCount();
    return () => {
      disconnectRealtime();
    };
  }, [
    hasHydrated,
    isAuthenticated,
    connectRealtime,
    disconnectRealtime,
    loadUnreadCount,
  ]);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [open]);

  if (!isAuthenticated) return null;

  return (
    <div ref={rootRef} className="relative">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label="Notifications"
        className="relative"
        onClick={() => setOpen((v) => !v)}
      >
        <Bell className="h-4 w-4" />
        <UnreadBadge count={unreadCount} />
      </Button>
      <NotificationDropdown open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
