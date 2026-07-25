"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Button } from "@/components/ui/button";
import { getSuggestions } from "@/services/profile";

type SuggestedUsersProps = {
  title?: string;
  className?: string;
};

export function SuggestedUsers({
  title = "People you may know",
  className,
}: SuggestedUsersProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["user-suggestions"],
    queryFn: getSuggestions,
  });

  if (isLoading || !data?.length) return null;

  return (
    <aside className={className}>
      <h2 className="font-[family-name:var(--font-fraunces)] text-lg font-semibold">
        {title}
      </h2>
      <ul className="mt-3 space-y-3">
        {data.slice(0, 5).map((user) => (
          <li
            key={user.username}
            className="flex items-center gap-3 rounded-xl border border-border/50 bg-card/60 px-3 py-2.5"
          >
            <ProfileAvatar
              name={user.name}
              username={user.username}
              src={user.avatar}
              size="sm"
              href={`/u/${user.username}`}
            />
            <div className="min-w-0 flex-1">
              <Link
                href={`/u/${user.username}`}
                className="block truncate text-sm font-semibold hover:underline"
              >
                {user.name}
              </Link>
              {user.headline ? (
                <p className="truncate text-xs text-muted-foreground">{user.headline}</p>
              ) : (
                <p className="truncate text-xs text-muted-foreground">@{user.username}</p>
              )}
            </div>
            <Button asChild size="sm" variant="outline">
              <Link href={`/u/${user.username}`}>View</Link>
            </Button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
