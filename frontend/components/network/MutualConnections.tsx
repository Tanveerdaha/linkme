"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { getMutualConnections } from "@/services/network";

type MutualConnectionsProps = {
  username: string;
};

export function MutualConnections({ username }: MutualConnectionsProps) {
  const { data } = useQuery({
    queryKey: ["mutual", username],
    queryFn: () => getMutualConnections(username),
    enabled: Boolean(username),
  });

  if (!data?.count) return null;

  return (
    <section className="rounded-xl border border-border/60 bg-card/60 px-4 py-3">
      <p className="text-sm text-muted-foreground">
        {data.count} mutual {data.count === 1 ? "connection" : "connections"}
      </p>
      <ul className="mt-2 flex flex-wrap gap-2">
        {data.users.slice(0, 6).map((user) => (
          <li key={user.username}>
            <Link
              href={`/u/${user.username}`}
              className="inline-flex items-center gap-1.5 rounded-full border border-border/50 bg-background/60 py-1 pl-1 pr-2.5 text-xs hover:bg-muted/40"
              title={user.name}
            >
              <ProfileAvatar
                name={user.name}
                username={user.username}
                src={user.avatar}
                size="sm"
                className="h-6 w-6 border-0"
              />
              {user.name.split(" ")[0]}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
