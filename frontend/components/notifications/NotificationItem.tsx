"use client";

import Link from "next/link";
import {
  Heart,
  MessageCircle,
  UserPlus,
  Users,
  MessageSquare,
  type LucideIcon,
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { notificationHref } from "@/services/notifications";
import type { AppNotification } from "@/types/notifications";

type NotificationItemProps = {
  notification: AppNotification;
  onClick?: (notification: AppNotification) => void;
  compact?: boolean;
};

const TYPE_ICONS: Record<string, LucideIcon> = {
  POST_REACTION: Heart,
  COMMENT_REACTION: Heart,
  POST_COMMENT: MessageCircle,
  COMMENT_REPLY: MessageCircle,
  CONNECTION_REQUEST: UserPlus,
  CONNECTION_ACCEPTED: UserPlus,
  MESSAGE_RECEIVED: MessageSquare,
};

function timeAgo(iso: string) {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return "";
  }
}

export function NotificationItem({
  notification,
  onClick,
  compact,
}: NotificationItemProps) {
  const href = notificationHref(notification) || "/notifications";
  const TypeIcon = TYPE_ICONS[notification.type] ?? Users;
  const name = notification.sender?.name || notification.sender?.username || "";
  const initial = name.charAt(0).toUpperCase() || "N";

  return (
    <Link
      href={href}
      onClick={() => onClick?.(notification)}
      className={cn(
        "flex gap-3 px-4 py-3 transition-colors hover:bg-muted/50",
        !notification.is_read && "bg-primary/5",
        compact && "py-2.5",
      )}
    >
      <div className="relative shrink-0">
        <Avatar className="h-10 w-10">
          {notification.sender?.avatar ? (
            <AvatarImage src={notification.sender.avatar} alt={name} />
          ) : null}
          <AvatarFallback>{initial}</AvatarFallback>
        </Avatar>
        <span className="absolute -bottom-0.5 -right-0.5 rounded-full bg-card p-0.5 text-primary">
          <TypeIcon className="h-3 w-3" />
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "text-sm leading-snug",
            !notification.is_read && "font-medium",
          )}
        >
          {notification.message}
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          {timeAgo(notification.created_at)}
        </p>
      </div>
      {!notification.is_read ? (
        <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-primary" />
      ) : null}
    </Link>
  );
}
