"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ConnectionButton } from "@/components/network/ConnectionButton";
import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getMutualConnections, getNetworkSuggestions } from "@/services/network";
import { cn } from "@/lib/utils";

type PeopleSuggestionsProps = {
  limit?: number;
  className?: string;
  id?: string;
};

function MutualLine({ username }: { username: string }) {
  const { data } = useQuery({
    queryKey: ["mutual", username],
    queryFn: () => getMutualConnections(username),
    enabled: Boolean(username),
  });
  if (!data?.count) return null;
  return (
    <p className="mt-1 text-xs text-muted-foreground">
      {data.count} mutual {data.count === 1 ? "connection" : "connections"}
    </p>
  );
}

export function PeopleSuggestions({
  limit = 4,
  className,
  id = "people-suggestions",
}: PeopleSuggestionsProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["network-discover"],
    queryFn: getNetworkSuggestions,
  });

  if (isLoading) {
    return (
      <section id={id} className={cn("space-y-3", className)}>
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold tracking-tight">People you may know</h2>
        </div>
        <div className="flex justify-center py-8">
          <Loader label="Loading suggestions" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section id={id} className={cn("space-y-3", className)}>
        <h2 className="text-lg font-semibold tracking-tight">People you may know</h2>
        <p className="text-sm text-destructive">
          {getApiErrorMessage(error, "Could not load suggestions")}
        </p>
      </section>
    );
  }

  const users = (data || []).slice(0, limit);
  if (!users.length) return null;

  return (
    <section id={id} className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold tracking-tight">People you may know</h2>
        <Link
          href="/network/discover"
          className="text-sm font-medium text-primary hover:underline"
        >
          See all
        </Link>
      </div>

      <ul className="flex gap-3 overflow-x-auto pb-1 md:grid md:grid-cols-2 md:overflow-visible md:pb-0 lg:grid-cols-4">
        {users.map((user) => (
          <li
            key={user.username}
            className="w-[220px] shrink-0 rounded-xl border border-border/70 bg-card p-4 shadow-sm md:w-auto"
          >
            <div className="flex flex-col items-center text-center">
              <ProfileAvatar
                name={user.name}
                username={user.username}
                src={user.avatar}
                size="md"
                href={`/u/${user.username}`}
              />
              <Link
                href={`/u/${user.username}`}
                className="mt-3 line-clamp-1 text-sm font-semibold hover:underline"
              >
                {user.name}
              </Link>
              <p className="truncate text-xs text-muted-foreground">
                @{user.username}
              </p>
              {user.headline ? (
                <p className="mt-1 line-clamp-2 text-xs text-foreground/80">
                  {user.headline}
                </p>
              ) : null}
              <MutualLine username={user.username} />
              <div className="mt-3 w-full">
                <ConnectionButton
                  username={user.username}
                  size="sm"
                  className="w-full"
                />
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
