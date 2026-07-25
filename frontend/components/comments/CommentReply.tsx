"use client";

import { useState } from "react";

import { CommentItem } from "@/components/comments/CommentItem";
import type { Comment } from "@/types";

type CommentReplyProps = {
  replies: Comment[];
  onDeleted?: () => void;
  /** How many replies to show before requiring expand. */
  previewCount?: number;
};

/** Nested replies under a top-level comment (one level deep). */
export function CommentReply({
  replies,
  onDeleted,
  previewCount = 2,
}: CommentReplyProps) {
  const [expanded, setExpanded] = useState(false);

  if (!replies?.length) return null;

  const hidden = Math.max(0, replies.length - previewCount);
  const visible = expanded || hidden === 0 ? replies : replies.slice(0, previewCount);

  return (
    <div className="mt-2 space-y-2.5 border-l border-border/40 pl-3 sm:pl-4">
      {!expanded && hidden > 0 ? (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="text-xs font-medium text-primary hover:underline"
        >
          View replies ({replies.length})
        </button>
      ) : null}
      {visible.map((reply) => (
        <CommentItem key={reply.id} comment={reply} isReply onDeleted={onDeleted} />
      ))}
      {expanded && hidden > 0 ? (
        <button
          type="button"
          onClick={() => setExpanded(false)}
          className="text-xs text-muted-foreground hover:underline"
        >
          Hide replies
        </button>
      ) : null}
    </div>
  );
}

/** @deprecated Prefer CommentReply. */
export function ReplyList(props: CommentReplyProps) {
  return <CommentReply {...props} />;
}
