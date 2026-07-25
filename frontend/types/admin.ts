/** Phase 9 — Admin dashboard types. */

export type AdminRoleName =
  | "SUPER_ADMIN"
  | "MODERATOR"
  | "SUPPORT_ADMIN"
  | "ANALYST";

export type AdminPermission =
  | "VIEW_DASHBOARD"
  | "VIEW_USERS"
  | "MANAGE_USERS"
  | "SUSPEND_USERS"
  | "DELETE_USERS"
  | "VIEW_CONTENT"
  | "REMOVE_CONTENT"
  | "RESTORE_CONTENT"
  | "VIEW_REPORTS"
  | "MANAGE_REPORTS"
  | "VIEW_MODERATION"
  | "TAKE_MODERATION_ACTION"
  | "VIEW_ANALYTICS"
  | "VIEW_AUDIT"
  | "EXPORT_DATA"
  | "MANAGE_ADMINS";

export type AdminMe = {
  id: string;
  username: string;
  email: string;
  role: AdminRoleName;
  permissions: AdminPermission[];
  is_superuser: boolean;
};

export type DashboardOverview = {
  users: { total: number; active_today: number };
  content: { posts: number; comments: number };
  network: { connections: number };
  reports: { pending: number };
};

export type AnalyticsTrends = {
  user_growth: { date: string; count: number }[];
  content_growth: { date: string; count: number }[];
  reports_trend: { date: string; count: number }[];
  comments_trend: { date: string; count: number }[];
};

export type AnalyticsMetrics = {
  daily_active_users: number;
  new_registrations: number;
  posts_created: number;
  comments: number;
  messages: number;
  reports: number;
  registrations_7d: number;
  posts_7d: number;
};

export type AdminUser = {
  id: string;
  username: string;
  email: string;
  status: "ACTIVE" | "SUSPENDED" | "INACTIVE" | "DELETED";
  is_verified: boolean;
  is_staff: boolean;
  created_at: string;
  avatar: string | null;
};

export type AdminUserDetail = {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  status: string;
  is_verified: boolean;
  is_staff: boolean;
  is_suspended: boolean;
  suspended_until: string | null;
  suspension_reason: string;
  is_deleted: boolean;
  created_at: string;
  posts_count: number;
  reports_count: number;
  connections_count: number;
  profile: { headline?: string; bio?: string; location?: string };
  admin_role: { role: string; permissions: string[] } | null;
  moderation_history: ModerationHistoryItem[];
  recent_activity: AuditLogItem[];
};

export type AdminPost = {
  id: string;
  author: string;
  content: string;
  visibility: string;
  status: string;
  reports: number;
  created_at: string;
  published_at: string | null;
};

export type AdminComment = {
  id: string;
  author: string;
  post_id: string;
  content: string;
  status: string;
  created_at: string;
};

export type AdminReport = {
  id: string;
  reporter: string;
  reason: string;
  target: string;
  reported_user: string | null;
  content_type_label: string;
  object_id: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  previous_reports?: AdminReport[];
  actions?: ModerationHistoryItem[];
};

export type ModerationHistoryItem = {
  id: string;
  admin: string;
  action: string;
  reason: string;
  target_type: string;
  target_id: string;
  date: string;
  created_at: string;
};

export type AuditLogItem = {
  id: string;
  user: string;
  action: string;
  object_type: string;
  object_id: string;
  object: string;
  metadata: Record<string, unknown>;
  time: string;
  created_at: string;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
