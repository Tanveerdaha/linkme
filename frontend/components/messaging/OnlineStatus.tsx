"use client";

import { cn } from "@/lib/utils";

type OnlineStatusProps = {
  online?: boolean;
  className?: string;
  showLabel?: boolean;
};

export function OnlineStatus({
  online = false,
  className,
  showLabel = true,
}: OnlineStatusProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs", className)}>
      <span
        className={cn(
          "h-2 w-2 rounded-full",
          online ? "bg-primary animate-soft-pulse" : "bg-muted-foreground/40",
        )}
        aria-hidden
      />
      {showLabel ? (
        <span className={online ? "text-primary" : "text-muted-foreground"}>
          {online ? "Online" : "Offline"}
        </span>
      ) : null}
    </span>
  );
}
