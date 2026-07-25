"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";

import { BottomNav } from "@/components/layout/bottom-nav";
import { ChatWindow } from "@/components/messaging/ChatWindow";
import { ConversationList } from "@/components/messaging/ConversationList";
import { useMessageStore } from "@/stores/messageStore";

export default function ConversationPage() {
  const params = useParams<{ conversationId: string }>();
  const conversationId = params.conversationId;

  const loadConversations = useMessageStore((s) => s.loadConversations);
  const openConversation = useMessageStore((s) => s.openConversation);
  const conversations = useMessageStore((s) => s.conversations);
  const conversationsLoading = useMessageStore((s) => s.conversationsLoading);
  const activeConversation = useMessageStore((s) => s.activeConversation);
  const messages = useMessageStore((s) => s.messages);
  const messagesLoading = useMessageStore((s) => s.messagesLoading);
  const hasMoreMessages = useMessageStore((s) => s.hasMoreMessages);
  const loadMoreMessages = useMessageStore((s) => s.loadMoreMessages);
  const sendMessage = useMessageStore((s) => s.sendMessage);
  const startTyping = useMessageStore((s) => s.startTyping);
  const stopTyping = useMessageStore((s) => s.stopTyping);
  const onlineUsers = useMessageStore((s) => s.onlineUsers);
  const typingUsers = useMessageStore((s) => s.typingUsers);
  const closeActiveConversation = useMessageStore((s) => s.closeActiveConversation);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (!conversationId) return;
    void openConversation(conversationId);
    return () => {
      closeActiveConversation();
    };
  }, [conversationId, openConversation, closeActiveConversation]);

  const participantUsername = activeConversation?.participant?.username;
  const typingUsername =
    participantUsername && typingUsers[participantUsername]
      ? participantUsername
      : null;

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
          <aside className="hidden border-border/70 md:block md:border-r">
            <ConversationList
              conversations={conversations}
              loading={conversationsLoading}
              activeId={conversationId}
              onlineUsers={onlineUsers}
            />
          </aside>
          <section className="flex h-[calc(100dvh-3.5rem-4rem)] flex-col md:h-full">
            <ChatWindow
              conversation={activeConversation}
              messages={messages}
              loading={messagesLoading}
              hasMore={hasMoreMessages}
              typingUsername={typingUsername}
              isOnline={
                participantUsername
                  ? Boolean(onlineUsers[participantUsername])
                  : false
              }
              onSend={async (payload) => {
                await sendMessage(payload);
              }}
              onTypingStart={startTyping}
              onTypingStop={stopTyping}
              onLoadMore={() => void loadMoreMessages()}
              showBack
            />
          </section>
        </div>
      </main>
      <div className="md:hidden">
        <BottomNav active="/messages" />
      </div>
    </>
  );
}
