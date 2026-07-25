"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { RemoveConnectionModal } from "@/components/network/RemoveConnectionModal";
import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import type { ConnectionListItem } from "@/services/network";
import * as networkApi from "@/services/network";
import { cn } from "@/lib/utils";

type ConnectionCardProps = {
  user: ConnectionListItem;
  onRemoved?: (username: string) => void;
  className?: string;
};

export function ConnectionCard({
  user,
  onRemoved,
  className,
}: ConnectionCardProps) {
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);

  async function confirmRemove() {
    setPending(true);
    try {
      await networkApi.removeConnection(user.username);
      toast.success("Connection removed");
      setOpen(false);
      onRemoved?.(user.username);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not remove connection"));
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <article
        className={cn(
          "flex items-center gap-3 rounded-xl border border-border/70 bg-card px-3 py-3 shadow-sm",
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
          {user.headline ? (
            <p className="mt-0.5 line-clamp-1 text-sm text-foreground/80">
              {user.headline}
            </p>
          ) : null}
        </div>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => setOpen(true)}
        >
          Remove
        </Button>
      </article>

      <RemoveConnectionModal
        open={open}
        onOpenChange={setOpen}
        name={user.name}
        username={user.username}
        pending={pending}
        onConfirm={() => void confirmRemove()}
      />
    </>
  );
}
