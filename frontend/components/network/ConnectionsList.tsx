"use client";

import { ConnectionCard } from "@/components/network/ConnectionCard";
import type { ConnectionListItem } from "@/services/network";

type ConnectionsListProps = {
  connections: ConnectionListItem[];
  emptyMessage?: string;
  onRemoved?: (username: string) => void;
};

export function ConnectionsList({
  connections,
  emptyMessage = "No connections yet.",
  onRemoved,
}: ConnectionsListProps) {
  if (!connections.length) {
    return (
      <p className="rounded-xl border border-dashed border-border/70 px-5 py-10 text-center text-sm text-muted-foreground">
        {emptyMessage}
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {connections.map((user) => (
        <li key={user.username}>
          <ConnectionCard user={user} onRemoved={onRemoved} />
        </li>
      ))}
    </ul>
  );
}
