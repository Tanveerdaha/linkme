"use client";

import { toast } from "sonner";

import { NetworkCard } from "@/components/network/NetworkCard";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import type { ConnectionRequest } from "@/services/network";

type ConnectionRequestCardProps = {
  request: ConnectionRequest;
  direction: "received" | "sent";
  onAccept?: (id: string, username: string) => Promise<void>;
  onReject?: (id: string, username: string) => Promise<void>;
  onCancel?: (id: string, username: string) => Promise<void>;
};

export function ConnectionRequestCard({
  request,
  direction,
  onAccept,
  onReject,
  onCancel,
}: ConnectionRequestCardProps) {
  async function handle(action?: (id: string, username: string) => Promise<void>) {
    if (!action) return;
    try {
      await action(request.id, request.user.username);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not update request"));
    }
  }

  const actions =
    direction === "received" ? (
      <div className="flex shrink-0 gap-2">
        <Button size="sm" onClick={() => void handle(onAccept)}>
          Accept
        </Button>
        <Button size="sm" variant="outline" onClick={() => void handle(onReject)}>
          Ignore
        </Button>
      </div>
    ) : (
      <Button size="sm" variant="secondary" onClick={() => void handle(onCancel)}>
        Cancel
      </Button>
    );

  return (
    <NetworkCard
      user={request.user}
      subtitle={request.message || request.user.headline}
      meta={new Date(request.created_at).toLocaleDateString()}
      actions={actions}
    />
  );
}
