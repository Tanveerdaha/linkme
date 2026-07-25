/** Shared domain types for LinkMe Phase 2. */

export type ApiError = {
  detail?: string;
  message?: string;
  code?: string;
  [key: string]: unknown;
};

export type AuthUser = {
  id: string;
  username: string;
  email: string;
  phone_number?: string;
  is_staff?: boolean;
};

export type UserSummary = {
  id: string;
  username: string;
  displayName?: string;
  avatarUrl?: string | null;
};

export type MeProfile = {
  id: string;
  username: string;
  email: string;
  phone_number?: string;
  first_name: string;
  last_name: string;
  name: string;
  avatar: string | null;
  cover_image: string | null;
  bio: string;
  headline: string;
  location: string;
  website: string;
  interests: string[];
  pronouns: string;
  birth_date: string | null;
  social_links: Record<string, string>;
  profile_visibility: "PUBLIC" | "PRIVATE";
  connection_visibility?: "PUBLIC" | "PRIVATE" | "CONNECTIONS_ONLY";
  completion?: ProfileCompletion;
  statistics?: ProfileStatistics;
  created_at: string;
};

export type PublicProfile = {
  id?: string;
  username: string;
  name: string;
  avatar: string | null;
  cover_image: string | null;
  bio: string;
  headline: string;
  location: string;
  website: string;
  interests: string[];
  pronouns?: string;
  social_links?: Record<string, string>;
  joined_date: string;
  statistics?: ProfileStatistics;
  is_private?: boolean;
};

export type ProfileStatistics = {
  posts: number;
  media: number;
  profile_views?: number;
};

export type ProfileCompletion = {
  percentage: number;
  missing: string[];
};

export type ProfileMediaItem = {
  id: string;
  media_type: MediaType;
  url: string | null;
  thumbnail_url: string | null;
  post_id: string;
  created_at: string;
  width: number | null;
  height: number | null;
  duration?: number | null;
  processing_status: MediaProcessingStatus;
};

export type ProfileMediaGallery = {
  images: ProfileMediaItem[];
  videos: ProfileMediaItem[];
};

export type ActivityItem = {
  type: "POST_CREATED" | "COMMENT_CREATED" | "REACTION_CREATED";
  content: string;
  created_at: string;
  ref_id?: string;
  post_id?: string;
  reaction_type?: string;
};

export type UserSearchResult = {
  username: string;
  name: string;
  avatar: string | null;
  headline: string;
  location?: string;
};

export type SuggestedUser = {
  username: string;
  name: string;
  avatar: string | null;
  headline: string;
};

export type PageResult<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type LoginResponse = {
  access: string;
  refresh: string;
  user: AuthUser;
};

export type SignupResponse = {
  message: string;
  email: string;
};

export type PostVisibility = "PUBLIC" | "PRIVATE" | "CONNECTIONS_ONLY";
export type PostStatus = "DRAFT" | "PUBLISHED" | "DELETED";
export type MediaType = "IMAGE" | "VIDEO";
export type MediaProcessingStatus = "PENDING" | "PROCESSING" | "READY" | "FAILED";

export type PostAuthor = {
  username: string;
  name: string;
  avatar: string | null;
  headline?: string;
};

export type PostMedia = {
  id: string;
  media_type: MediaType;
  url: string | null;
  thumbnail_url: string | null;
  order: number;
  processing_status: MediaProcessingStatus;
  width: number | null;
  height: number | null;
  duration: number | null;
  file_size: number | null;
  created_at: string;
};

export type Post = {
  id: string;
  author: PostAuthor;
  content: string;
  visibility: PostVisibility;
  status: PostStatus;
  media: PostMedia[];
  reaction_count: number;
  comment_count: number;
  user_reacted: boolean;
  created_at: string;
  updated_at: string;
  published_at: string | null;
};

export type CommentAuthor = {
  username: string;
  name: string;
  avatar: string | null;
};

export type Comment = {
  id: string;
  author: CommentAuthor;
  content: string;
  status: "ACTIVE" | "DELETED";
  parent: string | null;
  reaction_count: number;
  user_reacted: boolean;
  replies: Comment[];
  created_at: string;
  updated_at: string;
};

export type ReactionResult = {
  reacted: boolean;
  reaction_type?: string;
  count: number;
};

export type ReactionSummary = {
  total: number;
  heart: number;
};

export type SharePayload = {
  url: string;
  title: string;
};

export type CursorPage<T> = {
  next: string | null;
  previous: string | null;
  results: T[];
};
