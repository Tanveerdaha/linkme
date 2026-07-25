/** Messaging domain types. */

export type MessageParticipant = {
  username: string;
  name: string;
  avatar: string | null;
  headline: string;
  is_online?: boolean;
};

export type ConversationListItem = {
  id: string;
  participant: MessageParticipant | null;
  last_message: string | null;
  last_message_at: string | null;
  unread_count: number;
  is_muted?: boolean;
};

export type ConversationDetail = {
  id: string;
  participant: MessageParticipant | null;
  created_at: string;
  is_muted?: boolean;
};

export type MessageType = "TEXT" | "IMAGE" | "VIDEO" | "FILE" | "VOICE" | "LINK";

export type MessageMetadata = {
  url?: string;
  title?: string;
  filename?: string;
  duration_seconds?: number;
  [key: string]: unknown;
};

export type ChatMessage = {
  id: string;
  sender: string;
  content: string;
  message_type: MessageType;
  attachment?: string | null;
  metadata?: MessageMetadata;
  created_at: string;
  updated_at?: string;
  is_deleted: boolean;
  status?: "SENT" | "DELIVERED" | "READ" | null;
  conversation_id?: string;
};

export type SendMessagePayload = {
  content?: string;
  attachment?: File | null;
  message_type?: MessageType;
  metadata?: MessageMetadata;
};
