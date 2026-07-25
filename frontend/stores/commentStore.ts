import { create } from "zustand";

import * as commentsApi from "@/services/comments";
import type { Comment } from "@/types";

type CommentState = {
  postId: string | null;
  comments: Comment[];
  loading: boolean;
  loadingMore: boolean;
  cursor: string | null;
  hasMore: boolean;
  error: string | null;
  openForPost: (postId: string) => Promise<void>;
  loadMore: () => Promise<void>;
  createComment: (content: string) => Promise<Comment>;
  addReply: (parentId: string, content: string) => Promise<Comment>;
  deleteComment: (commentId: string) => Promise<void>;
  updateCommentReaction: (
    commentId: string,
    reacted: boolean,
    count: number,
  ) => void;
  reset: () => void;
};

const initial = {
  postId: null as string | null,
  comments: [] as Comment[],
  loading: false,
  loadingMore: false,
  cursor: null as string | null,
  hasMore: false,
  error: null as string | null,
};

function patchCommentTree(
  comments: Comment[],
  commentId: string,
  updater: (c: Comment) => Comment,
): Comment[] {
  return comments.map((comment) => {
    if (comment.id === commentId) return updater(comment);
    if (comment.replies?.length) {
      return {
        ...comment,
        replies: comment.replies.map((reply) =>
          reply.id === commentId ? updater(reply) : reply,
        ),
      };
    }
    return comment;
  });
}

export const useCommentStore = create<CommentState>((set, get) => ({
  ...initial,
  openForPost: async (postId) => {
    set({
      postId,
      comments: [],
      loading: true,
      error: null,
      cursor: null,
      hasMore: false,
    });
    try {
      const page = await commentsApi.getComments(postId);
      set({
        comments: page.results,
        cursor: commentsApi.cursorFromUrl(page.next),
        hasMore: Boolean(page.next),
        loading: false,
      });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load comments",
      });
    }
  },
  loadMore: async () => {
    const { postId, cursor, loadingMore, hasMore } = get();
    if (!postId || !cursor || loadingMore || !hasMore) return;
    set({ loadingMore: true });
    try {
      const page = await commentsApi.getComments(postId, cursor);
      set((state) => {
        const seen = new Set(state.comments.map((c) => c.id));
        const merged = [...state.comments];
        for (const comment of page.results) {
          if (!seen.has(comment.id)) merged.push(comment);
        }
        return {
          comments: merged,
          cursor: commentsApi.cursorFromUrl(page.next),
          hasMore: Boolean(page.next),
          loadingMore: false,
        };
      });
    } catch {
      set({ loadingMore: false });
    }
  },
  createComment: async (content) => {
    const { postId } = get();
    if (!postId) throw new Error("No post selected");
    const comment = await commentsApi.createComment(postId, content);
    set((state) => ({ comments: [...state.comments, { ...comment, replies: [] }] }));
    return comment;
  },
  addReply: async (parentId, content) => {
    const reply = await commentsApi.replyComment(parentId, content);
    set((state) => ({
      comments: state.comments.map((comment) =>
        comment.id === parentId
          ? { ...comment, replies: [...(comment.replies || []), reply] }
          : comment,
      ),
    }));
    return reply;
  },
  deleteComment: async (commentId) => {
    await commentsApi.deleteComment(commentId);
    set((state) => {
      const isTopLevel = state.comments.some((c) => c.id === commentId);
      if (isTopLevel) {
        return {
          comments: state.comments
            .map((c) => {
              if (c.id !== commentId) return c;
              const replies = c.replies || [];
              if (replies.length === 0) return null;
              return { ...c, status: "DELETED" as const, content: "[deleted]" };
            })
            .filter((c): c is Comment => c !== null),
        };
      }
      return {
        comments: state.comments.map((c) => ({
          ...c,
          replies: (c.replies || []).filter((r) => r.id !== commentId),
        })),
      };
    });
  },
  updateCommentReaction: (commentId, reacted, count) => {
    set((state) => ({
      comments: patchCommentTree(state.comments, commentId, (c) => ({
        ...c,
        user_reacted: reacted,
        reaction_count: count,
      })),
    }));
  },
  reset: () => set({ ...initial }),
}));
