"use client";

import Link from "next/link";

import { OnlineStatus } from "@/components/messaging/OnlineStatus";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import type { ConversationListItem } from "@/types/messaging";

type ConversationItemProps = {
  conversation: ConversationListItem;
  active?: boolean;
  isOnline?: boolean;
};

function formatPreviewTime(iso: string | null) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) {
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export function ConversationItem({
  conversation,
  active,
  isOnline,
}: ConversationItemProps) {
  const participant = conversation.participant;
  const name = participant?.name || participant?.username || "Unknown";
  const initial = name.charAt(0).toUpperCase();

  return (
    <Link
      href={`/messages/${conversation.id}`}
      className={cn(
        "flex items-center gap-3 border-b border-border/40 px-4 py-3 transition-colors hover:bg-muted/50",
        active && "bg-muted/70",
      )}
    >
      <div className="relative">
        <Avatar className="h-11 w-11">
          {participant?.avatar ? (
            <AvatarImage src={participant.avatar} alt={name} />
          ) : null}
          <AvatarFallback>{initial}</AvatarFallback>
        </Avatar>
        <span className="absolute bottom-0 right-0">
          <OnlineStatus online={isOnline} showLabel={false} />
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate text-sm font-medium">{name}</p>
          <span className="shrink-0 text-[11px] text-muted-foreground">
            {formatPreviewTime(conversation.last_message_at)}
          </span>
        </div>
        <div className="mt-0.5 flex items-center justify-between gap-2">
          <p className="truncate text-xs text-muted-foreground">
            {conversation.last_message || "No messages yet"}
          </p>
          {conversation.unread_count > 0 ? (
            <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-semibold text-primary-foreground">
              {conversation.unread_count}
            </span>
          ) : null}
        </div>
      </div>
    </Link>
  );
}
