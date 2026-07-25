"use client";

import { useEffect, useRef } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { MessageBubble } from "@/components/messaging/MessageBubble";
import { MessageInput } from "@/components/messaging/MessageInput";
import { OnlineStatus } from "@/components/messaging/OnlineStatus";
import { TypingIndicator } from "@/components/messaging/TypingIndicator";
import { SafetyMenu } from "@/components/moderation/SafetyMenu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Loader } from "@/components/ui/loader";
import { useAuthStore } from "@/stores/authStore";
import type { ChatMessage, ConversationDetail, SendMessagePayload } from "@/types/messaging";

type ChatWindowProps = {
  conversation: ConversationDetail | null;
  messages: ChatMessage[];
  loading?: boolean;
  hasMore?: boolean;
  typingUsername?: string | null;
  isOnline?: boolean;
  onSend: (payload: SendMessagePayload) => Promise<void> | void;
  onTypingStart?: () => void;
  onTypingStop?: () => void;
  onLoadMore?: () => void;
  showBack?: boolean;
};

export function ChatWindow({
  conversation,
  messages,
  loading,
  hasMore,
  typingUsername,
  isOnline,
  onSend,
  onTypingStart,
  onTypingStop,
  onLoadMore,
  showBack = false,
}: ChatWindowProps) {
  const me = useAuthStore((s) => s.user?.username);
  const bottomRef = useRef<HTMLDivElement>(null);
  const participant = conversation?.participant;
  const name = participant?.name || participant?.username || "Chat";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, typingUsername]);

  if (!conversation) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-6 text-center">
        <p className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold">
          Select a conversation
        </p>
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">
          Choose someone from your list to start messaging in real time.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="flex items-center gap-3 border-b border-border/70 px-3 py-3 sm:px-4">
        {showBack ? (
          <Button asChild variant="ghost" size="sm" className="shrink-0 px-2 md:hidden">
            <Link href="/messages" aria-label="Back to messages">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
        ) : null}
        <Avatar className="h-10 w-10">
          {participant?.avatar ? (
            <AvatarImage src={participant.avatar} alt={name} />
          ) : null}
          <AvatarFallback>{name.charAt(0).toUpperCase()}</AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium leading-tight">{name}</p>
          {participant?.headline ? (
            <p className="truncate text-xs text-muted-foreground">{participant.headline}</p>
          ) : null}
          <OnlineStatus online={isOnline} className="mt-0.5" />
        </div>
        {participant?.username ? (
          <div className="ml-auto">
            <SafetyMenu
              contentType="USER"
              objectId={participant.username}
              username={participant.username}
              label={`@${participant.username}`}
              showBlock
            />
          </div>
        ) : null}
      </header>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-4 sm:px-4">
        {hasMore ? (
          <div className="flex justify-center">
            <Button variant="ghost" size="sm" onClick={onLoadMore}>
              Load earlier messages
            </Button>
          </div>
        ) : null}
        {loading ? (
          <div className="flex justify-center py-10">
            <Loader />
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              isOwn={message.sender === me}
            />
          ))
        )}
        <TypingIndicator username={typingUsername || undefined} />
        <div ref={bottomRef} />
      </div>

      <MessageInput
        onSend={onSend}
        onTypingStart={onTypingStart}
        onTypingStop={onTypingStop}
        className="md:static sticky bottom-0 z-10"
      />
    </div>
  );
}
