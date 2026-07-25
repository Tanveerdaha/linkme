import api from "@/services/api";
import type { CursorPage, Post } from "@/types";

function cursorParam(cursor?: string | null) {
  return cursor ? { cursor } : {};
}

/** Extract the `cursor` query value from a DRF absolute `next`/`previous` URL. */
export function cursorFromUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.searchParams.get("cursor");
  } catch {
    const match = /[?&]cursor=([^&]+)/.exec(url);
    return match ? decodeURIComponent(match[1]) : null;
  }
}

export async function getPublicFeed(cursor?: string | null): Promise<CursorPage<Post>> {
  const { data } = await api.get<CursorPage<Post>>("/feed/public/", {
    params: cursorParam(cursor),
  });
  return data;
}

export async function getUserFeed(cursor?: string | null): Promise<CursorPage<Post>> {
  const { data } = await api.get<CursorPage<Post>>("/feed/", {
    params: cursorParam(cursor),
  });
  return data;
}
