"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import * as networkApi from "@/services/network";
import { useAuthStore } from "@/stores/authStore";
import { useMessageStore } from "@/stores/messageStore";
import { cn } from "@/lib/utils";

type MessageButtonProps = {
  username: string;
  className?: string;
};

export function MessageButton({ username, className }: MessageButtonProps) {
  const router = useRouter();
  const authUser = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const startConversation = useMessageStore((s) => s.startConversation);
  const [connected, setConnected] = useState(false);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !username || authUser?.username === username) return;
    let cancelled = false;
    networkApi
      .getConnectionStatus(username)
      .then((data) => {
        if (!cancelled) setConnected(data.status === "CONNECTED");
      })
      .catch(() => {
        if (!cancelled) setConnected(false);
      });
    return () => {
      cancelled = true;
    };
  }, [username, isAuthenticated, authUser?.username]);

  if (!isAuthenticated || authUser?.username === username) return null;

  if (!connected) {
    return (
      <Button
        type="button"
        variant="ghost"
        className={cn(className)}
        disabled
        title="Connect to message"
      >
        Message
      </Button>
    );
  }

  return (
    <Button
      type="button"
      variant="ghost"
      className={cn(className)}
      disabled={pending}
      onClick={() => {
        setPending(true);
        void startConversation(username)
          .then((conversation) => {
            router.push(`/messages/${conversation.id}`);
          })
          .catch((err) => {
            toast.error(getApiErrorMessage(err, "Could not start conversation"));
          })
          .finally(() => setPending(false));
      }}
    >
      {pending ? "Opening…" : "Message"}
    </Button>
  );
}
