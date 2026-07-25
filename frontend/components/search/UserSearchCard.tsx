"use client";

import Link from "next/link";

import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Button } from "@/components/ui/button";
import type { SuggestedUser, UserSearchResult } from "@/types";
import { cn } from "@/lib/utils";

type SearchUser = SuggestedUser | UserSearchResult;

type UserSearchCardProps = {
  user: SearchUser;
  className?: string;
  viewLabel?: string;
};

export function UserSearchCard({
  user,
  className,
  viewLabel = "View",
}: UserSearchCardProps) {
  return (
    <article
      className={cn(
        "flex items-center gap-3 rounded-xl border border-border/60 bg-card px-3 py-3 transition-colors hover:bg-muted/30",
        className,
      )}
    >
      <ProfileAvatar
        name={user.name}
        username={user.username}
        src={user.avatar}
        size="md"
        href={`/u/${user.username}`}
      />
      <div className="min-w-0 flex-1">
        <Link
          href={`/u/${user.username}`}
          className="block truncate font-semibold hover:underline"
        >
          {user.name}
        </Link>
        <p className="truncate text-sm text-muted-foreground">@{user.username}</p>
        {"headline" in user && user.headline ? (
          <p className="mt-0.5 line-clamp-1 text-sm text-foreground/80">
            {user.headline}
          </p>
        ) : null}
        {"location" in user && user.location ? (
          <p className="mt-0.5 text-xs text-muted-foreground">{user.location}</p>
        ) : null}
      </div>
      <Button asChild size="sm" variant="outline">
        <Link href={`/u/${user.username}`}>{viewLabel}</Link>
      </Button>
    </article>
  );
}
