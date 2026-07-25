"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { toast } from "sonner";

import { PostActions } from "@/components/feed/PostActions";
import { PostContent } from "@/components/feed/PostContent";
import { PostHeader } from "@/components/feed/PostHeader";
import { PostMedia } from "@/components/feed/PostMedia";
import { useIsMobile } from "@/hooks/use-is-mobile";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/services/api";
import { getPostShare } from "@/services/comments";
import * as reactionsApi from "@/services/reactions";
import { useAuthStore } from "@/stores/authStore";
import { useFeedStore } from "@/stores/feedStore";
import type { Post } from "@/types";

const CommentSection = dynamic(
  () =>
    import("@/components/comments/CommentSection").then((m) => m.CommentSection),
  {
    ssr: false,
    loading: () => (
      <div className="mt-3 h-24 animate-pulse rounded-lg bg-muted/40" aria-hidden />
    ),
  },
);

type PostCardProps = {
  post: Post;
  className?: string;
};

export function PostCard({ post, className }: PostCardProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const updatePost = useFeedStore((s) => s.updatePost);

  const [pendingReaction, setPendingReaction] = useState(false);
  const [commentsOpen, setCommentsOpen] = useState(false);
  const isMobile = useIsMobile();

  const reactionCount = post.reaction_count ?? 0;
  const commentCount = post.comment_count ?? 0;
  const userReacted = Boolean(post.user_reacted);

  async function toggleReaction() {
    if (!isAuthenticated) {
      toast.error("Login required to react to posts");
      return;
    }
    if (pendingReaction) return;

    const prev = {
      user_reacted: userReacted,
      reaction_count: reactionCount,
    };
    const nextReacted = !userReacted;
    updatePost({
      ...post,
      user_reacted: nextReacted,
      reaction_count: Math.max(0, reactionCount + (nextReacted ? 1 : -1)),
    });
    setPendingReaction(true);
    try {
      const result = nextReacted
        ? await reactionsApi.addPostReaction(post.id)
        : await reactionsApi.removePostReaction(post.id);
      updatePost({
        ...post,
        user_reacted: result.reacted,
        reaction_count: result.count,
      });
    } catch (err) {
      updatePost({
        ...post,
        user_reacted: prev.user_reacted,
        reaction_count: prev.reaction_count,
      });
      toast.error(getApiErrorMessage(err, "Could not update reaction"));
    } finally {
      setPendingReaction(false);
    }
  }

  async function handleShare() {
    try {
      const share = await getPostShare(post.id);
      if (typeof navigator !== "undefined" && navigator.share) {
        try {
          await navigator.share({ title: share.title, url: share.url });
          return;
        } catch {
          // Fall through to clipboard.
        }
      }
      await navigator.clipboard.writeText(share.url);
      toast.success("Link copied");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not share post"));
    }
  }

  return (
    <article
      className={cn(
        "animate-fade-up border-b border-border/60 py-4 transition-colors hover:bg-muted/20",
        className,
      )}
    >
      <div className="px-1 sm:px-2">
        <PostHeader post={post} />
        <PostContent content={post.content} />
        <PostMedia media={post.media} />
        <PostActions
          reactionCount={reactionCount}
          commentCount={commentCount}
          userReacted={userReacted}
          pendingReaction={pendingReaction}
          onToggleReaction={() => void toggleReaction()}
          onComment={() => setCommentsOpen(true)}
          onShare={() => void handleShare()}
        />
        {commentsOpen ? (
          <CommentSection
            postId={post.id}
            open={commentsOpen}
            onClose={() => setCommentsOpen(false)}
            variant={isMobile ? "sheet" : "inline"}
          />
        ) : null}
      </div>
    </article>
  );
}
