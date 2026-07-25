import { create } from "zustand";

import type { Post } from "@/types";

type FeedMode = "public" | "user" | "author";

type FeedState = {
  mode: FeedMode;
  posts: Post[];
  loading: boolean;
  loadingMore: boolean;
  cursor: string | null;
  hasMore: boolean;
  error: string | null;
  setMode: (mode: FeedMode) => void;
  setLoading: (loading: boolean) => void;
  setLoadingMore: (loadingMore: boolean) => void;
  setError: (error: string | null) => void;
  setPosts: (posts: Post[], cursor: string | null, hasMore: boolean) => void;
  appendPosts: (posts: Post[], cursor: string | null, hasMore: boolean) => void;
  prependPost: (post: Post) => void;
  removePost: (id: string) => void;
  updatePost: (post: Post) => void;
  resetFeed: () => void;
};

const initial = {
  mode: "public" as FeedMode,
  posts: [] as Post[],
  loading: false,
  loadingMore: false,
  cursor: null as string | null,
  hasMore: true,
  error: null as string | null,
};

export const useFeedStore = create<FeedState>((set) => ({
  ...initial,
  setMode: (mode) => set({ mode }),
  setLoading: (loading) => set({ loading }),
  setLoadingMore: (loadingMore) => set({ loadingMore }),
  setError: (error) => set({ error }),
  setPosts: (posts, cursor, hasMore) => set({ posts, cursor, hasMore, error: null }),
  appendPosts: (posts, cursor, hasMore) =>
    set((state) => {
      const seen = new Set(state.posts.map((p) => p.id));
      const merged = [...state.posts];
      for (const post of posts) {
        if (!seen.has(post.id)) merged.push(post);
      }
      return { posts: merged, cursor, hasMore };
    }),
  prependPost: (post) =>
    set((state) => ({
      posts: [post, ...state.posts.filter((p) => p.id !== post.id)],
    })),
  removePost: (id) => set((state) => ({ posts: state.posts.filter((p) => p.id !== id) })),
  updatePost: (post) =>
    set((state) => ({
      posts: state.posts.map((p) => (p.id === post.id ? post : p)),
    })),
  resetFeed: () => set({ ...initial }),
}));
