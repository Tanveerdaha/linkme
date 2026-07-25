"use client";

import { ConversationItem } from "@/components/messaging/ConversationItem";
import { Loader } from "@/components/ui/loader";
import type { ConversationListItem } from "@/types/messaging";

type ConversationListProps = {
  conversations: ConversationListItem[];
  loading?: boolean;
  activeId?: string | null;
  onlineUsers?: Record<string, boolean>;
};

export function ConversationList({
  conversations,
  loading,
  activeId,
  onlineUsers = {},
}: ConversationListProps) {
  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader />
      </div>
    );
  }

  if (!conversations.length) {
    return (
      <div className="px-6 py-12 text-center">
        <p className="font-[family-name:var(--font-fraunces)] text-lg font-semibold">
          No conversations yet
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Message a connection from their profile to start chatting.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-y-auto">
      {conversations.map((conversation) => {
        const username = conversation.participant?.username;
        return (
          <ConversationItem
            key={conversation.id}
            conversation={conversation}
            active={conversation.id === activeId}
            isOnline={username ? Boolean(onlineUsers[username]) : false}
          />
        );
      })}
    </div>
  );
}
