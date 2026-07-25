import api from "@/services/api";
import type { Comment, CursorPage, SharePayload } from "@/types";

export async function getComments(
  postId: string,
  cursor?: string | null,
): Promise<CursorPage<Comment>> {
  const { data } = await api.get<CursorPage<Comment>>(`/posts/${postId}/comments/`, {
    params: cursor ? { cursor } : undefined,
  });
  return data;
}

export async function createComment(postId: string, content: string): Promise<Comment> {
  const { data } = await api.post<Comment>(`/posts/${postId}/comments/`, { content });
  return data;
}

export async function replyComment(commentId: string, content: string): Promise<Comment> {
  const { data } = await api.post<Comment>(`/comments/${commentId}/reply/`, { content });
  return data;
}

export async function updateComment(commentId: string, content: string): Promise<Comment> {
  const { data } = await api.patch<Comment>(`/comments/${commentId}/`, { content });
  return data;
}

export async function deleteComment(commentId: string): Promise<void> {
  await api.delete(`/comments/${commentId}/`);
}

export async function getPostShare(postId: string): Promise<SharePayload> {
  const { data } = await api.get<SharePayload>(`/posts/${postId}/share/`);
  return data;
}

export function cursorFromUrl(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.searchParams.get("cursor");
  } catch {
    const match = url.match(/[?&]cursor=([^&]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  }
}
