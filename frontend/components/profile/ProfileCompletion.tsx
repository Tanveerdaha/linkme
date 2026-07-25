"use client";

import Link from "next/link";

import type { ProfileCompletion } from "@/types";
import { cn } from "@/lib/utils";

const LABELS: Record<string, string> = {
  avatar: "profile photo",
  cover_image: "cover image",
  headline: "headline",
  bio: "bio",
  location: "location",
  website: "website",
  interests: "interests",
};

type ProfileCompletionProps = {
  completion?: ProfileCompletion | null;
  className?: string;
};

export function ProfileCompletionBanner({
  completion,
  className,
}: ProfileCompletionProps) {
  if (!completion || completion.percentage >= 100) return null;

  const missing = completion.missing
    .slice(0, 3)
    .map((key) => LABELS[key] || key)
    .join(", ");

  return (
    <div
      className={cn(
        "animate-fade-up rounded-xl border border-border/70 bg-card px-4 py-3",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium">
            Profile {completion.percentage}% complete
          </p>
          {missing ? (
            <p className="mt-0.5 text-xs text-muted-foreground">
              Add {missing} to strengthen your identity.
            </p>
          ) : null}
        </div>
        <Link
          href="/profile/edit"
          className="shrink-0 text-sm font-medium text-primary hover:underline"
        >
          Complete
        </Link>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${completion.percentage}%` }}
        />
      </div>
    </div>
  );
}
