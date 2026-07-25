/** Notification domain types. */

export type NotificationSender = {
  username: string;
  name: string;
  avatar: string | null;
};

export type AppNotification = {
  id: string;
  type: string;
  notification_type?: string;
  sender: NotificationSender | null;
  message: string;
  object_type: string;
  object_id: string;
  is_read: boolean;
  created_at: string;
  read_at?: string | null;
};

export type NotificationPreferences = {
  post_reactions_enabled: boolean;
  comments_enabled: boolean;
  connection_enabled: boolean;
  messages_enabled: boolean;
};

export type UnreadCount = {
  count: number;
};
