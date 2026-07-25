"use client";

import { cn } from "@/lib/utils";

export function ReactionSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("h-8 w-20 animate-pulse rounded-md bg-muted/70", className)}
      aria-hidden
    />
  );
}
