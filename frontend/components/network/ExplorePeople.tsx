"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Button } from "@/components/ui/button";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { searchUsers } from "@/services/search";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";

type ExplorePeopleProps = {
  limit?: number;
  className?: string;
};

export function ExplorePeople({ limit = 6, className }: ExplorePeopleProps) {
  const me = useAuthStore((s) => s.user?.username);
  const { data, isLoading, error } = useQuery({
    queryKey: ["explore-people"],
    queryFn: () => searchUsers({ page_size: 24 }),
  });

  if (isLoading) {
    return (
      <section className={cn("space-y-3", className)}>
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Explore People</h2>
          <p className="text-sm text-muted-foreground">
            Discover other users on LinkMe
          </p>
        </div>
        <div className="flex justify-center py-8">
          <Loader label="Loading people" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className={cn("space-y-3", className)}>
        <h2 className="text-lg font-semibold tracking-tight">Explore People</h2>
        <p className="text-sm text-destructive">
          {getApiErrorMessage(error, "Could not load people")}
        </p>
      </section>
    );
  }

  const users = (data?.results || [])
    .filter((u) => u.username !== me)
    .slice(0, limit);

  if (!users.length) return null;

  return (
    <section className={cn("space-y-3", className)}>
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Explore People</h2>
          <p className="text-sm text-muted-foreground">
            Discover other users on LinkMe
          </p>
        </div>
        <Link
          href="/search/users"
          className="text-sm font-medium text-primary hover:underline"
        >
          Search more
        </Link>
      </div>

      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {users.map((user) => (
          <li
            key={user.username}
            className="flex items-center gap-3 rounded-xl border border-border/70 bg-card px-3 py-3 shadow-sm"
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
              <p className="truncate text-sm text-muted-foreground">
                @{user.username}
              </p>
            </div>
            <Button asChild size="sm" variant="outline">
              <Link href={`/u/${user.username}`}>View Profile</Link>
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
