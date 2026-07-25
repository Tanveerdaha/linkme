"use client";

import { useEffect } from "react";

import { BottomNav } from "@/components/layout/bottom-nav";
import { ConversationList } from "@/components/messaging/ConversationList";
import { ChatWindow } from "@/components/messaging/ChatWindow";
import { useMessageStore } from "@/stores/messageStore";

export default function MessagesPage() {
  const loadConversations = useMessageStore((s) => s.loadConversations);
  const conversations = useMessageStore((s) => s.conversations);
  const conversationsLoading = useMessageStore((s) => s.conversationsLoading);
  const onlineUsers = useMessageStore((s) => s.onlineUsers);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  return (
    <>
      <main className="mx-auto w-full max-w-6xl px-0 pb-20 md:px-4 md:py-8 md:pb-10">
        <div className="mb-0 hidden px-4 pt-8 md:mb-6 md:block md:px-0 md:pt-0">
          <h1 className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight">
            Messages
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Private chats with your connections.
          </p>
        </div>

        <div className="overflow-hidden border-border/70 bg-card/80 md:grid md:h-[min(720px,75vh)] md:grid-cols-[320px_1fr] md:rounded-2xl md:border">
          <aside className="border-border/70 md:border-r">
            <div className="border-b border-border/70 px-4 py-3 md:hidden">
              <h1 className="font-[family-name:var(--font-fraunces)] text-xl font-semibold">
                Messages
              </h1>
            </div>
            <ConversationList
              conversations={conversations}
              loading={conversationsLoading}
              onlineUsers={onlineUsers}
            />
          </aside>
          <section className="hidden md:block">
            <ChatWindow
              conversation={null}
              messages={[]}
              onSend={async () => undefined}
            />
          </section>
        </div>
      </main>
      <BottomNav active="/messages" />
    </>
  );
}
