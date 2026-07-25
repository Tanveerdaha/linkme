"use client";

import { Heart } from "lucide-react";

import { cn } from "@/lib/utils";

type ReactionCountProps = {
  count: number;
  className?: string;
};

export function ReactionCount({ count, className }: ReactionCountProps) {
  if (count <= 0) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-sm text-muted-foreground",
        className,
      )}
    >
      <Heart className="h-3.5 w-3.5 fill-rose-500 text-rose-500" />
      <span className="tabular-nums">
        {count} {count === 1 ? "heart" : "hearts"}
      </span>
    </span>
  );
}
