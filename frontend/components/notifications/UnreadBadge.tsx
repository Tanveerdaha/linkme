"use client";

import { cn } from "@/lib/utils";

type UnreadBadgeProps = {
  count: number;
  className?: string;
};

export function UnreadBadge({ count, className }: UnreadBadgeProps) {
  if (count <= 0) return null;
  const label = count > 99 ? "99+" : String(count);
  return (
    <span
      className={cn(
        "absolute -right-1 -top-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground",
        className,
      )}
    >
      {label}
    </span>
  );
}
