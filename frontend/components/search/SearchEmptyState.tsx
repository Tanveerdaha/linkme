"use client";

import { Users } from "lucide-react";

import { cn } from "@/lib/utils";

type SearchEmptyStateProps = {
  className?: string;
};

export function SearchEmptyState({ className }: SearchEmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center rounded-2xl border border-border/70 bg-card/70 px-6 py-14 text-center",
        className,
      )}
    >
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
        <Users className="h-5 w-5" aria-hidden />
      </div>
      <p className="max-w-sm text-sm font-medium text-foreground">
        Start typing to discover people on LinkMe.
      </p>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        Search by name, username, headline, or location.
      </p>
    </div>
  );
}
