"use client";

import { Heart } from "lucide-react";

import { cn } from "@/lib/utils";

type ReactionButtonProps = {
  reacted: boolean;
  count?: number;
  disabled?: boolean;
  pending?: boolean;
  onToggle: () => void;
  size?: "sm" | "md";
  className?: string;
  showLabel?: boolean;
};

export function ReactionButton({
  reacted,
  count,
  disabled,
  pending,
  onToggle,
  size = "md",
  className,
  showLabel = true,
}: ReactionButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || pending}
      onClick={onToggle}
      aria-pressed={reacted}
      aria-label={reacted ? "Remove heart" : "Heart"}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
        reacted
          ? "text-rose-600 hover:bg-rose-500/10 dark:text-rose-400"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
        size === "sm" && "px-2 py-1 text-xs",
        (disabled || pending) && "opacity-60",
        className,
      )}
    >
      <Heart
        className={cn(
          size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4",
          "transition-transform",
          reacted && "fill-current scale-110",
          pending && "animate-soft-pulse",
        )}
      />
      {showLabel ? <span>{reacted ? "Heart" : "Heart"}</span> : null}
      {typeof count === "number" && count > 0 ? (
        <span className="tabular-nums">{count}</span>
      ) : null}
    </button>
  );
}
