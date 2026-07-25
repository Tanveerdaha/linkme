"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import type { ConnectionStatus } from "@/services/network";
import * as networkApi from "@/services/network";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";

type ConnectionButtonProps = {
  username: string;
  initialStatus?: ConnectionStatus | null;
  className?: string;
  size?: "sm" | "default";
};

export function ConnectionButton({
  username,
  initialStatus,
  className,
  size = "default",
}: ConnectionButtonProps) {
  const authUser = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [status, setStatus] = useState<ConnectionStatus | null>(initialStatus || null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !username || authUser?.username === username) return;
    let cancelled = false;
    networkApi
      .getConnectionStatus(username)
      .then((data) => {
        if (!cancelled) setStatus(data);
      })
      .catch(() => {
        /* ignore */
      });
    return () => {
      cancelled = true;
    };
  }, [username, isAuthenticated, authUser?.username]);

  if (!isAuthenticated || authUser?.username === username || status?.is_self) {
    return null;
  }

  async function run(action: () => Promise<ConnectionStatus>) {
    setPending(true);
    try {
      const next = await action();
      setStatus(next);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not update connection"));
    } finally {
      setPending(false);
    }
  }

  const current = status?.status || "NONE";

  if (current === "CONNECTED") {
    return (
      <Button
        type="button"
        variant="outline"
        size={size}
        disabled={pending}
        className={cn(className)}
        onClick={() =>
          void run(async () => {
            if (!window.confirm(`Remove connection with @${username}?`)) {
              return status || { status: "CONNECTED", can_connect: false };
            }
            return networkApi.removeConnection(username);
          })
        }
      >
        Connected
      </Button>
    );
  }

  if (current === "REQUEST_SENT") {
    return (
      <Button
        type="button"
        variant="secondary"
        size={size}
        disabled={pending || !status?.connection_id}
        className={cn(className)}
        onClick={() => {
          if (!status?.connection_id) return;
          void run(() => networkApi.cancelRequest(status.connection_id!));
        }}
      >
        Request sent
      </Button>
    );
  }

  if (current === "REQUEST_RECEIVED") {
    return (
      <div className={cn("flex gap-2", className)}>
        <Button
          type="button"
          size={size}
          disabled={pending || !status?.connection_id}
          onClick={() => {
            if (!status?.connection_id) return;
            void run(() => networkApi.acceptRequest(status.connection_id!));
          }}
        >
          Accept
        </Button>
        <Button
          type="button"
          variant="outline"
          size={size}
          disabled={pending || !status?.connection_id}
          onClick={() => {
            if (!status?.connection_id) return;
            void run(() => networkApi.rejectRequest(status.connection_id!));
          }}
        >
          Ignore
        </Button>
      </div>
    );
  }

  if (current === "BLOCKED") {
    return null;
  }

  return (
    <Button
      type="button"
      size={size}
      disabled={pending || status?.can_connect === false}
      className={cn(className)}
      onClick={() => void run(() => networkApi.sendConnectionRequest(username))}
    >
      + Connect
    </Button>
  );
}

/** Lightweight link-styled fallback for guests. */
export function ConnectLoginPrompt({ className }: { className?: string }) {
  return (
    <Button asChild variant="outline" className={className}>
      <Link href="/login">Log in to connect</Link>
    </Button>
  );
}
