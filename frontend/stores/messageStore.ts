import { create } from "zustand";

import * as messagesApi from "@/services/messages";
import {
  connectSocket,
  disconnectSocket,
  sendEvent,
  subscribe,
} from "@/services/socket";
import { useAuthStore } from "@/stores/authStore";
import type {
  ChatMessage,
  ConversationDetail,
  ConversationListItem,
  SendMessagePayload,
} from "@/types/messaging";

type MessageState = {
  conversations: ConversationListItem[];
  conversationsLoading: boolean;
  messages: ChatMessage[];
  messagesLoading: boolean;
  messagesCursor: string | null;
  hasMoreMessages: boolean;
  activeConversation: ConversationDetail | null;
  onlineUsers: Record<string, boolean>;
  typingUsers: Record<string, boolean>;
  error: string | null;
  loadConversations: () => Promise<void>;
  loadMessages: (conversationId: string) => Promise<void>;
  loadMoreMessages: () => Promise<void>;
  openConversation: (conversationId: string) => Promise<void>;
  startConversation: (username: string) => Promise<ConversationDetail>;
  sendMessage: (payload: SendMessagePayload | string, attachment?: File | null) => Promise<void>;
  markRead: (messageId?: string) => void;
  startTyping: () => void;
  stopTyping: () => void;
  deleteMessage: (messageId: string) => Promise<void>;
  closeActiveConversation: () => void;
  reset: () => void;
};

const initial = {
  conversations: [] as ConversationListItem[],
  conversationsLoading: false,
  messages: [] as ChatMessage[],
  messagesLoading: false,
  messagesCursor: null as string | null,
  hasMoreMessages: false,
  activeConversation: null as ConversationDetail | null,
  onlineUsers: {} as Record<string, boolean>,
  typingUsers: {} as Record<string, boolean>,
  error: null as string | null,
};

let unsubscribers: Array<() => void> = [];

function clearSocketSubscriptions() {
  unsubscribers.forEach((unsub) => unsub());
  unsubscribers = [];
}

function upsertMessage(list: ChatMessage[], message: ChatMessage): ChatMessage[] {
  if (list.some((m) => m.id === message.id)) {
    return list.map((m) => (m.id === message.id ? { ...m, ...message } : m));
  }
  return [...list, message].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );
}

export const useMessageStore = create<MessageState>((set, get) => ({
  ...initial,

  loadConversations: async () => {
    set({ conversationsLoading: true, error: null });
    try {
      const page = await messagesApi.getConversations();
      set({ conversations: page.results, conversationsLoading: false });
    } catch (err) {
      set({
        conversationsLoading: false,
        error: err instanceof Error ? err.message : "Failed to load conversations",
      });
    }
  },

  loadMessages: async (conversationId) => {
    set({
      messages: [],
      messagesLoading: true,
      messagesCursor: null,
      hasMoreMessages: false,
      error: null,
    });
    try {
      const page = await messagesApi.getMessages(conversationId);
      const chronological = [...page.results].reverse();
      set({
        messages: chronological,
        messagesCursor: messagesApi.cursorFromUrl(page.next),
        hasMoreMessages: Boolean(page.next),
        messagesLoading: false,
      });
    } catch (err) {
      set({
        messagesLoading: false,
        error: err instanceof Error ? err.message : "Failed to load messages",
      });
    }
  },

  loadMoreMessages: async () => {
    const { activeConversation, messagesCursor, hasMoreMessages, messages } = get();
    if (!activeConversation || !hasMoreMessages || !messagesCursor) return;
    try {
      const page = await messagesApi.getMessages(
        activeConversation.id,
        messagesCursor,
      );
      const older = [...page.results].reverse();
      set({
        messages: [...older, ...messages],
        messagesCursor: messagesApi.cursorFromUrl(page.next),
        hasMoreMessages: Boolean(page.next),
      });
    } catch {
      // keep existing messages
    }
  },

  openConversation: async (conversationId) => {
    const token = useAuthStore.getState().accessToken;
    if (!token) return;

    clearSocketSubscriptions();
    disconnectSocket();
    set({ typingUsers: {} });

    const detail = await messagesApi.getConversation(conversationId);
    set({
      activeConversation: detail,
      onlineUsers: {
        ...get().onlineUsers,
        ...(detail.participant?.username
          ? {
              [detail.participant.username]: Boolean(detail.participant.is_online),
            }
          : {}),
      },
    });

    await get().loadMessages(conversationId);

    connectSocket(conversationId, token);

    unsubscribers = [
      subscribe("socket.open", () => {
        get().markRead();
      }),
      subscribe("message.receive", (payload) => {
        const message = payload.message as ChatMessage | undefined;
        if (!message) return;
        set((state) => ({
          messages: upsertMessage(state.messages, message),
        }));
        const me = useAuthStore.getState().user?.username;
        if (message.sender !== me) {
          get().markRead(message.id);
        }
        void get().loadConversations();
      }),
      subscribe("typing", (payload) => {
        const username = String(payload.user || "");
        const typing = Boolean(payload.typing);
        if (!username) return;
        set((state) => ({
          typingUsers: { ...state.typingUsers, [username]: typing },
        }));
      }),
      subscribe("presence", (payload) => {
        const username = String(payload.user || "");
        if (!username) return;
        set((state) => ({
          onlineUsers: {
            ...state.onlineUsers,
            [username]: Boolean(payload.online),
          },
        }));
      }),
      subscribe("message.read", (payload) => {
        const messageId = payload.message_id as string | null;
        const me = useAuthStore.getState().user?.username;
        set((state) => ({
          messages: state.messages.map((m) => {
            if (messageId && m.id !== messageId) return m;
            if (m.sender === me) return { ...m, status: "READ" };
            return m;
          }),
        }));
      }),
      subscribe("message.delivered", (payload) => {
        const messageId = String(payload.message_id || "");
        if (!messageId) return;
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === messageId && m.status === "SENT"
              ? { ...m, status: "DELIVERED" }
              : m,
          ),
        }));
      }),
    ];
  },

  startConversation: async (username) => {
    const detail = await messagesApi.createConversation(username);
    await get().loadConversations();
    return detail;
  },

  sendMessage: async (payloadOrContent, attachment = null) => {
    const { activeConversation } = get();
    if (!activeConversation) return;

    const payload: SendMessagePayload =
      typeof payloadOrContent === "string"
        ? { content: payloadOrContent, attachment }
        : payloadOrContent;

    const needsRest =
      Boolean(payload.attachment) ||
      (payload.message_type && payload.message_type !== "TEXT") ||
      Boolean(payload.metadata && Object.keys(payload.metadata).length);

    if (needsRest) {
      const message = await messagesApi.sendMessage(activeConversation.id, payload);
      set((state) => ({
        messages: upsertMessage(state.messages, message),
      }));
      void get().loadConversations();
      return;
    }

    if (payload.content?.trim()) {
      sendEvent({ type: "message.send", content: payload.content.trim() });
    }
  },

  markRead: (messageId) => {
    if (messageId) {
      sendEvent({ type: "message.read", message_id: messageId });
    } else {
      sendEvent({ type: "message.read" });
    }
  },

  startTyping: () => {
    sendEvent({ type: "typing.start" });
  },

  stopTyping: () => {
    sendEvent({ type: "typing.stop" });
  },

  deleteMessage: async (messageId) => {
    await messagesApi.deleteMessage(messageId);
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === messageId
          ? { ...m, is_deleted: true, content: "", attachment: null }
          : m,
      ),
    }));
  },

  closeActiveConversation: () => {
    clearSocketSubscriptions();
    disconnectSocket();
    set({
      activeConversation: null,
      messages: [],
      messagesCursor: null,
      hasMoreMessages: false,
      messagesLoading: false,
      typingUsers: {},
    });
  },

  reset: () => {
    clearSocketSubscriptions();
    disconnectSocket();
    set({ ...initial });
  },
}));
