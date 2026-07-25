/** Phase 8 — privacy, moderation, and account types. */

export type ProfileVisibility = "PUBLIC" | "PRIVATE";
export type PostVisibility = "PUBLIC" | "CONNECTIONS_ONLY" | "PRIVATE";
export type ConnectionVisibility = "PUBLIC" | "CONNECTIONS_ONLY" | "PRIVATE";
export type MessagePermission = "CONNECTIONS_ONLY" | "NOBODY";

export type PrivacySettings = {
  profile_visibility: ProfileVisibility;
  post_visibility: PostVisibility;
  connection_visibility: ConnectionVisibility;
  message_permission: MessagePermission;
  created_at?: string;
  updated_at?: string;
};

export type BlockedUser = {
  username: string;
  avatar: string | null;
  blocked_at: string;
  reason?: string;
};

export type ReportContentType = "USER" | "POST" | "COMMENT" | "MESSAGE";

export type ReportReason =
  | "SPAM"
  | "HARASSMENT"
  | "HATE_SPEECH"
  | "VIOLENCE"
  | "NUDITY"
  | "FAKE_ACCOUNT"
  | "OTHER";

export type ReportStatus = "PENDING" | "UNDER_REVIEW" | "RESOLVED" | "REJECTED";

export type Report = {
  id: string;
  content_type_label: ReportContentType;
  object_id: string;
  reason: ReportReason;
  description: string;
  status: ReportStatus;
  reported_username: string | null;
  created_at: string;
  updated_at: string;
};

export type ModerationActionType =
  | "WARNING"
  | "CONTENT_REMOVED"
  | "USER_SUSPENDED"
  | "USER_BANNED";

export type AccountStatus = {
  username: string;
  email: string;
  phone_number?: string;
  is_active: boolean;
  is_verified: boolean;
  is_suspended: boolean;
  suspended_until: string | null;
  suspension_reason: string;
  is_deleted: boolean;
  is_staff: boolean;
};

export type DataExportStatus = {
  id: string;
  status: "PENDING" | "PROCESSING" | "READY" | "FAILED" | "EXPIRED";
  download_url: string | null;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
  error_message: string | null;
};

export const REPORT_REASON_LABELS: Record<ReportReason, string> = {
  SPAM: "Spam",
  HARASSMENT: "Harassment",
  HATE_SPEECH: "Hate speech",
  VIOLENCE: "Violence",
  NUDITY: "Nudity",
  FAKE_ACCOUNT: "Fake account",
  OTHER: "Other",
};
