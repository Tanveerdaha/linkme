"use client";

import { MessageCircle, Share2 } from "lucide-react";

import { ReactionButton } from "@/components/reactions/ReactionButton";
import { ReactionCount } from "@/components/reactions/ReactionCount";

type PostActionsProps = {
  reactionCount: number;
  commentCount: number;
  userReacted: boolean;
  pendingReaction: boolean;
  onToggleReaction: () => void;
  onComment: () => void;
  onShare: () => void;
};

export function PostActions({
  reactionCount,
  commentCount,
  userReacted,
  pendingReaction,
  onToggleReaction,
  onComment,
  onShare,
}: PostActionsProps) {
  return (
    <>
      {(reactionCount > 0 || commentCount > 0) && (
        <div className="mt-2.5 flex items-center gap-3 text-sm text-muted-foreground">
          <ReactionCount count={reactionCount} />
          {commentCount > 0 ? (
            <button type="button" onClick={onComment} className="hover:underline">
              {commentCount} {commentCount === 1 ? "comment" : "comments"}
            </button>
          ) : null}
        </div>
      )}

      <div className="mt-1.5 flex gap-1">
        <ReactionButton
          reacted={userReacted}
          pending={pendingReaction}
          onToggle={onToggleReaction}
        />
        <button
          type="button"
          onClick={onComment}
          className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <MessageCircle className="h-4 w-4" />
          Comment
        </button>
        <button
          type="button"
          onClick={onShare}
          className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Share2 className="h-4 w-4" />
          Share
        </button>
      </div>
    </>
  );
}
