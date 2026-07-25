"use client";

import Link from "next/link";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export type MiniProfileUser = {
  name: string;
  username: string;
  avatar?: string | null;
};

type MiniProfileCardProps = {
  user: MiniProfileUser;
  connectionsCount: number;
  postsCount: number;
  className?: string;
};

function initials(name: string, username: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return (username.slice(0, 2) || "LM").toUpperCase();
}

export function MiniProfileCard({
  user,
  connectionsCount,
  postsCount,
  className,
}: MiniProfileCardProps) {
  return (
    <aside
      className={cn(
        "rounded-xl border border-border/70 bg-card p-5 shadow-sm",
        className,
      )}
    >
      <Link
        href={`/u/${user.username}`}
        className="flex flex-col items-center text-center outline-none transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-ring"
      >
        <Avatar className="h-16 w-16 border border-border/60">
          {user.avatar ? (
            <AvatarImage src={user.avatar} alt={user.name} />
          ) : null}
          <AvatarFallback className="bg-secondary text-base font-semibold text-secondary-foreground">
            {initials(user.name, user.username)}
          </AvatarFallback>
        </Avatar>

        <p className="mt-3 text-sm font-semibold text-foreground">
          {user.name || user.username}
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground">@{user.username}</p>
      </Link>

      <div className="mt-4 grid grid-cols-2 gap-2 border-t border-border/60 pt-4">
        <Link
          href="/network/connections"
          className="rounded-lg px-1 py-1 text-center transition-colors hover:bg-muted/60"
        >
          <p className="text-base font-semibold tabular-nums text-foreground">
            {connectionsCount}
          </p>
          <p className="text-[11px] text-muted-foreground">Connections</p>
        </Link>
        <Link
          href={`/u/${user.username}`}
          className="rounded-lg px-1 py-1 text-center transition-colors hover:bg-muted/60"
        >
          <p className="text-base font-semibold tabular-nums text-foreground">
            {postsCount}
          </p>
          <p className="text-[11px] text-muted-foreground">Posts</p>
        </Link>
      </div>
    </aside>
  );
}
