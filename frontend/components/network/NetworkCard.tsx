"use client";

import Link from "next/link";

import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Button } from "@/components/ui/button";
import type { NetworkUser } from "@/services/network";
import { cn } from "@/lib/utils";

type NetworkCardProps = {
  user: NetworkUser;
  subtitle?: string;
  meta?: string;
  actions?: React.ReactNode;
  className?: string;
};

export function NetworkCard({
  user,
  subtitle,
  meta,
  actions,
  className,
}: NetworkCardProps) {
  return (
    <article
      className={cn(
        "flex items-center gap-3 rounded-xl border border-border/60 bg-card/70 px-3 py-3",
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
        {(subtitle || user.headline) && (
          <p className="mt-0.5 line-clamp-1 text-sm text-foreground/80">
            {subtitle || user.headline}
          </p>
        )}
        {meta ? <p className="mt-0.5 text-xs text-muted-foreground">{meta}</p> : null}
      </div>
      {actions ?? (
        <Button asChild size="sm" variant="outline">
          <Link href={`/u/${user.username}`}>View</Link>
        </Button>
      )}
    </article>
  );
}
