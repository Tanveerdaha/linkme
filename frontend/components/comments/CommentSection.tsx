"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { toast } from "sonner";

import { CommentInput } from "@/components/comments/CommentInput";
import { CommentItem } from "@/components/comments/CommentItem";
import { CommentReply } from "@/components/comments/CommentReply";
import { CommentSkeleton } from "@/components/comments/CommentSkeleton";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";
import { useCommentStore } from "@/stores/commentStore";
import { useFeedStore } from "@/stores/feedStore";
import { cn } from "@/lib/utils";

const INITIAL_VISIBLE = 3;

type CommentSectionProps = {
  postId: string;
  open: boolean;
  onClose: () => void;
  variant?: "inline" | "sheet";
  className?: string;
};

export function CommentSection({
  postId,
  open,
  onClose,
  variant = "inline",
  className,
}: CommentSectionProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const {
    comments,
    loading,
    loadingMore,
    hasMore,
    error,
    openForPost,
    loadMore,
    createComment,
    reset,
  } = useCommentStore();
  const updatePost = useFeedStore((s) => s.updatePost);
  const [showAll, setShowAll] = useState(false);

  function bumpCommentCount(delta: number) {
    const post = useFeedStore.getState().posts.find((p) => p.id === postId);
    if (!post) return;
    updatePost({
      ...post,
      comment_count: Math.max(0, (post.comment_count || 0) + delta),
    });
  }

  useEffect(() => {
    if (!open) return;
    setShowAll(false);
    void openForPost(postId);
  }, [open, postId, openForPost]);

  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);

  if (!open) return null;

  async function handleCreate(content: string) {
    await createComment(content);
    bumpCommentCount(1);
  }

  const visibleComments =
    showAll || comments.length <= INITIAL_VISIBLE
      ? comments
      : comments.slice(0, INITIAL_VISIBLE);
  const hiddenCount = Math.max(0, comments.length - INITIAL_VISIBLE);

  const body = (
    <div className={cn("flex h-full flex-col", className)}>
      <header className="flex items-center justify-between border-b border-border/60 pb-2.5">
        <h3 className="text-sm font-semibold tracking-tight">Comments</h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Close comments"
        >
          <X className="h-4 w-4" />
        </button>
      </header>

      <div className="min-h-0 flex-1 space-y-3.5 overflow-y-auto py-3">
        {loading ? <CommentSkeleton /> : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {!loading && !error && comments.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No comments yet. Start the conversation.
          </p>
        ) : null}
        {visibleComments.map((comment) => (
          <div key={comment.id}>
            <CommentItem
              comment={comment}
              onReplyAdded={() => bumpCommentCount(1)}
              onDeleted={() => bumpCommentCount(-1)}
            />
            <CommentReply
              replies={comment.replies || []}
              onDeleted={() => bumpCommentCount(-1)}
            />
          </div>
        ))}
        {!showAll && hiddenCount > 0 ? (
          <button
            type="button"
            onClick={() => setShowAll(true)}
            className="text-sm font-medium text-primary hover:underline"
          >
            View all comments
          </button>
        ) : null}
        {showAll && hasMore ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={loadingMore}
            onClick={() => void loadMore()}
            className="w-full"
          >
            {loadingMore ? "Loading…" : "Load more comments"}
          </Button>
        ) : null}
      </div>

      <div className="border-t border-border/60 pt-3">
        {isAuthenticated ? (
          <CommentInput onSubmit={handleCreate} />
        ) : (
          <p className="text-sm text-muted-foreground">
            <button
              type="button"
              className="font-medium text-primary hover:underline"
              onClick={() => toast.error("Login required to comment")}
            >
              Log in
            </button>{" "}
            to join the conversation.
          </p>
        )}
      </div>
    </div>
  );

  if (variant === "sheet") {
    return (
      <div className="fixed inset-0 z-50 md:hidden">
        <button
          type="button"
          className="absolute inset-0 bg-black/45"
          aria-label="Dismiss"
          onClick={onClose}
        />
        <div className="absolute inset-x-0 bottom-0 max-h-[85vh] rounded-t-2xl border border-border bg-card p-4 shadow-lg animate-fade-up">
          {body}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-xl border border-border/60 bg-muted/20 px-3 py-3 sm:px-4">
      {body}
    </div>
  );
}
