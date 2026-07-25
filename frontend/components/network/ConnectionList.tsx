"use client";

import { toast } from "sonner";

import { ConnectionButton } from "@/components/network/ConnectionButton";
import { NetworkCard } from "@/components/network/NetworkCard";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import type { ConnectionListItem } from "@/services/network";
import * as networkApi from "@/services/network";

type ConnectionListProps = {
  connections: ConnectionListItem[];
  emptyMessage?: string;
  onRemoved?: (username: string) => void;
  showRemove?: boolean;
};

export function ConnectionList({
  connections,
  emptyMessage = "No connections yet.",
  onRemoved,
  showRemove = true,
}: ConnectionListProps) {
  if (!connections.length) {
    return (
      <p className="rounded-2xl border border-dashed border-border/70 px-5 py-10 text-center text-sm text-muted-foreground">
        {emptyMessage}
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {connections.map((user) => (
        <li key={user.username}>
          <NetworkCard
            user={user}
            meta={
              user.connected_at
                ? `Connected ${new Date(user.connected_at).toLocaleDateString()}`
                : undefined
            }
            actions={
              showRemove ? (
                <div className="flex shrink-0 gap-2">
                  <ConnectionButton username={user.username} size="sm" />
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={async () => {
                      if (!window.confirm(`Remove @${user.username}?`)) return;
                      try {
                        await networkApi.removeConnection(user.username);
                        onRemoved?.(user.username);
                        toast.success("Connection removed");
                      } catch (err) {
                        toast.error(getApiErrorMessage(err, "Could not remove"));
                      }
                    }}
                  >
                    Remove
                  </Button>
                </div>
              ) : (
                <ConnectionButton username={user.username} size="sm" />
              )
            }
          />
        </li>
      ))}
    </ul>
  );
}
