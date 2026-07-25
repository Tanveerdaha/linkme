import api from "@/services/api";
import type { CursorPage, PageResult } from "@/types";
import type {
  ChatMessage,
  ConversationDetail,
  ConversationListItem,
  SendMessagePayload,
} from "@/types/messaging";

export async function getConversations(
  page = 1,
): Promise<PageResult<ConversationListItem>> {
  const { data } = await api.get<PageResult<ConversationListItem>>(
    "/messages/conversations/",
    { params: { page } },
  );
  return data;
}

export async function createConversation(
  username: string,
): Promise<ConversationDetail> {
  const { data } = await api.post<ConversationDetail>("/messages/conversations/", {
    username,
  });
  return data;
}

export async function getConversation(
  conversationId: string,
): Promise<ConversationDetail> {
  const { data } = await api.get<ConversationDetail>(
    `/messages/conversations/${conversationId}/`,
  );
  return data;
}

export async function getMessages(
  conversationId: string,
  cursor?: string | null,
): Promise<CursorPage<ChatMessage>> {
  const { data } = await api.get<CursorPage<ChatMessage>>(
    `/messages/conversations/${conversationId}/messages/`,
    { params: cursor ? { cursor } : undefined },
  );
  return data;
}

export async function sendMessage(
  conversationId: string,
  payload: SendMessagePayload,
): Promise<ChatMessage> {
  const needsMultipart =
    Boolean(payload.attachment) ||
    payload.message_type === "IMAGE" ||
    payload.message_type === "VIDEO" ||
    payload.message_type === "FILE" ||
    payload.message_type === "VOICE";

  if (needsMultipart || payload.attachment) {
    const form = new FormData();
    if (payload.content) form.append("content", payload.content);
    if (payload.message_type) form.append("message_type", payload.message_type);
    if (payload.metadata) form.append("metadata", JSON.stringify(payload.metadata));
    if (payload.attachment) form.append("attachment", payload.attachment);
    const { data } = await api.post<ChatMessage>(
      `/messages/conversations/${conversationId}/messages/`,
      form,
      { headers: { "Content-Type": "multipart/form-data" }, timeout: 300_000 },
    );
    return data;
  }

  const { data } = await api.post<ChatMessage>(
    `/messages/conversations/${conversationId}/messages/`,
    {
      content: payload.content || "",
      message_type: payload.message_type || "TEXT",
      metadata: payload.metadata || {},
    },
  );
  return data;
}

export async function deleteMessage(messageId: string): Promise<void> {
  await api.delete(`/messages/${messageId}/`);
}

export async function muteConversation(
  conversationId: string,
  is_muted: boolean,
): Promise<ConversationDetail> {
  const { data } = await api.patch<ConversationDetail>(
    `/messages/conversations/${conversationId}/mute/`,
    { is_muted },
  );
  return data;
}

export function cursorFromUrl(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.searchParams.get("cursor");
  } catch {
    return null;
  }
}
