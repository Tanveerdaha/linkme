"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";

export type CommentInputProps = {
  placeholder?: string;
  submitLabel?: string;
  replyToName?: string;
  onSubmit: (content: string) => Promise<void>;
  onCancel?: () => void;
  autoFocus?: boolean;
  className?: string;
  compact?: boolean;
};

/** Shared composer for top-level comments and threaded replies. */
export function CommentInput({
  placeholder = "Write a comment…",
  submitLabel = "Comment",
  replyToName,
  onSubmit,
  onCancel,
  autoFocus,
  className,
  compact,
}: CommentInputProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isAuthenticated) {
      toast.error("Login required to comment");
      return;
    }
    const text = content.trim();
    if (!text || submitting) return;
    setSubmitting(true);
    try {
      await onSubmit(text);
      setContent("");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not post comment"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-2", className)}>
      {replyToName ? (
        <p className="text-xs text-muted-foreground">
          Replying to <span className="font-medium text-foreground">{replyToName}</span>
        </p>
      ) : null}
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        maxLength={2000}
        rows={compact ? 2 : 3}
        className={cn(
          "w-full resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm",
          "placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
      />
      <div className="flex items-center justify-end gap-2">
        {onCancel ? (
          <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        ) : null}
        <Button
          type="submit"
          size="sm"
          disabled={!content.trim() || submitting || !isAuthenticated}
        >
          {submitting ? "Posting…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}

/** @deprecated Prefer CommentInput — kept for existing imports. */
export const CommentComposer = CommentInput;
