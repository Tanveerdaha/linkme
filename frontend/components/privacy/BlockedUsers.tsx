"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { getApiErrorMessage } from "@/services/api";
import { usePrivacyStore } from "@/stores/privacyStore";

export function BlockedUsers() {
  const blockedUsers = usePrivacyStore((s) => s.blockedUsers);
  const loadBlockedUsers = usePrivacyStore((s) => s.loadBlockedUsers);
  const unblockUser = usePrivacyStore((s) => s.unblockUser);
  const [pending, setPending] = useState<string | null>(null);

  useEffect(() => {
    loadBlockedUsers().catch(() => {
      toast.error("Could not load blocked users");
    });
  }, [loadBlockedUsers]);

  async function handleUnblock(username: string) {
    setPending(username);
    try {
      await unblockUser(username);
      toast.success(`Unblocked @${username}`);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not unblock user"));
    } finally {
      setPending(null);
    }
  }

  if (blockedUsers.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">You haven&apos;t blocked anyone.</p>
    );
  }

  return (
    <ul className="divide-y divide-border/60">
      {blockedUsers.map((user) => (
        <li key={user.username} className="flex items-center justify-between gap-3 py-3">
          <div className="flex items-center gap-3">
            <Avatar className="h-9 w-9">
              {user.avatar ? <AvatarImage src={user.avatar} alt={user.username} /> : null}
              <AvatarFallback>{user.username.slice(0, 2).toUpperCase()}</AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-medium">@{user.username}</p>
              <p className="text-xs text-muted-foreground">
                Blocked {new Date(user.blocked_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={pending === user.username}
            onClick={() => handleUnblock(user.username)}
          >
            Unblock
          </Button>
        </li>
      ))}
    </ul>
  );
}
