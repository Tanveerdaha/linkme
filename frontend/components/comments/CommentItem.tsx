"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { CommentInput } from "@/components/comments/CommentInput";
import { SafetyMenu } from "@/components/moderation/SafetyMenu";
import { ReactionButton } from "@/components/reactions/ReactionButton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { getApiErrorMessage } from "@/services/api";
import * as reactionsApi from "@/services/reactions";
import { useAuthStore } from "@/stores/authStore";
import { useCommentStore } from "@/stores/commentStore";
import type { Comment } from "@/types";
import { cn } from "@/lib/utils";

function initials(name: string, username: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (username.slice(0, 2) || "LM").toUpperCase();
}

type CommentItemProps = {
  comment: Comment;
  isReply?: boolean;
  onReplyAdded?: () => void;
  onDeleted?: () => void;
};

export function CommentItem({
  comment,
  isReply = false,
  onReplyAdded,
  onDeleted,
}: CommentItemProps) {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const addReply = useCommentStore((s) => s.addReply);
  const deleteComment = useCommentStore((s) => s.deleteComment);
  const updateCommentReaction = useCommentStore((s) => s.updateCommentReaction);

  const [showReply, setShowReply] = useState(false);
  const [pendingReaction, setPendingReaction] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const isOwner = user?.username === comment.author.username;
  const isDeleted = comment.status === "DELETED";

  async function toggleReaction() {
    if (!isAuthenticated) {
      toast.error("Login required to react to comments");
      return;
    }
    if (isDeleted || pendingReaction) return;

    const prevReacted = comment.user_reacted;
    const prevCount = comment.reaction_count;
    const nextReacted = !prevReacted;
    const nextCount = Math.max(0, prevCount + (nextReacted ? 1 : -1));
    updateCommentReaction(comment.id, nextReacted, nextCount);
    setPendingReaction(true);
    try {
      const result = nextReacted
        ? await reactionsApi.addCommentReaction(comment.id)
        : await reactionsApi.removeCommentReaction(comment.id);
      updateCommentReaction(comment.id, result.reacted, result.count);
    } catch (err) {
      updateCommentReaction(comment.id, prevReacted, prevCount);
      toast.error(getApiErrorMessage(err, "Could not update reaction"));
    } finally {
      setPendingReaction(false);
    }
  }

  async function handleDelete() {
    if (!isOwner || deleting) return;
    setDeleting(true);
    try {
      await deleteComment(comment.id);
      onDeleted?.();
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not delete comment"));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className={cn("flex gap-2.5", isReply && "ml-1 sm:ml-2")}>
      <Link href={`/u/${comment.author.username}`} className="shrink-0">
        <Avatar className={cn(isReply ? "h-7 w-7" : "h-8 w-8")}>
          {comment.author.avatar ? (
            <AvatarImage src={comment.author.avatar} alt={comment.author.name} />
          ) : null}
          <AvatarFallback>
            {initials(comment.author.name, comment.author.username)}
          </AvatarFallback>
        </Avatar>
      </Link>
      <div className="min-w-0 flex-1">
        <div className="leading-snug">
          <Link
            href={`/u/${comment.author.username}`}
            className="text-sm font-semibold hover:underline"
          >
            {comment.author.name}
          </Link>
          <p
            className={cn(
              "mt-0.5 whitespace-pre-wrap text-sm leading-relaxed",
              isDeleted && "italic text-muted-foreground",
            )}
          >
            {comment.content}
          </p>
        </div>
        {!isDeleted ? (
          <div className="mt-1 flex flex-wrap items-center gap-1">
            <ReactionButton
              reacted={comment.user_reacted}
              count={comment.reaction_count}
              pending={pendingReaction}
              onToggle={toggleReaction}
              size="sm"
              showLabel={false}
            />
            {!isReply ? (
              <button
                type="button"
                onClick={() => {
                  if (!isAuthenticated) {
                    toast.error("Login required to reply");
                    return;
                  }
                  setShowReply((v) => !v);
                }}
                className="rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                Reply
              </button>
            ) : null}
            {isOwner ? (
              <button
                type="button"
                disabled={deleting}
                onClick={handleDelete}
                className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
            ) : (
              <SafetyMenu
                contentType="COMMENT"
                objectId={String(comment.id)}
                username={comment.author.username}
                label={`comment by ${comment.author.name}`}
              />
            )}
          </div>
        ) : null}
        {showReply && !isReply ? (
          <CommentInput
            className="mt-2"
            compact
            autoFocus
            replyToName={comment.author.name}
            placeholder="Write a reply…"
            submitLabel="Reply"
            onCancel={() => setShowReply(false)}
            onSubmit={async (content) => {
              await addReply(comment.id, content);
              setShowReply(false);
              onReplyAdded?.();
            }}
          />
        ) : null}
      </div>
    </div>
  );
}
