import api from "@/services/api";
import type { CursorPage, Post, PostVisibility } from "@/types";

function multipartConfig(onUploadProgress?: (pct: number) => void) {
  return {
    headers: { "Content-Type": "multipart/form-data" },
    transformRequest: [
      (body: unknown, headers?: Record<string, unknown>) => {
        if (headers && typeof headers === "object") {
          delete headers["Content-Type"];
        }
        return body;
      },
    ],
    onUploadProgress: onUploadProgress
      ? (event: { loaded: number; total?: number }) => {
          if (!event.total) return;
          onUploadProgress(Math.round((event.loaded / event.total) * 100));
        }
      : undefined,
    timeout: 5 * 60_000,
  };
}

export async function createPost(input: {
  content: string;
  visibility?: PostVisibility;
  media?: File[];
  onUploadProgress?: (pct: number) => void;
}): Promise<Post> {
  const form = new FormData();
  form.append("content", input.content);
  form.append("visibility", input.visibility || "PUBLIC");
  for (const file of input.media || []) {
    form.append("media", file);
  }
  const { data } = await api.post<Post>("/posts/", form, multipartConfig(input.onUploadProgress));
  return data;
}

export async function getPost(id: string): Promise<Post> {
  const { data } = await api.get<Post>(`/posts/${id}/`);
  return data;
}

export async function updatePost(
  id: string,
  payload: { content?: string; visibility?: PostVisibility },
): Promise<Post> {
  const { data } = await api.patch<Post>(`/posts/${id}/`, payload);
  return data;
}

export async function deletePost(id: string): Promise<void> {
  await api.delete(`/posts/${id}/`);
}

export async function getAuthorPosts(
  username: string,
  cursor?: string | null,
): Promise<CursorPage<Post>> {
  const { data } = await api.get<CursorPage<Post>>("/posts/", {
    params: { username, ...(cursor ? { cursor } : {}) },
  });
  return data;
}
