"use client";

import Link from "next/link";
import { Check, X } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import * as networkApi from "@/services/network";
import { cn } from "@/lib/utils";

type ConnectionRequestsProps = {
  limit?: number;
  className?: string;
  id?: string;
};

function MutualCount({ username }: { username: string }) {
  const { data } = useQuery({
    queryKey: ["mutual", username],
    queryFn: () => networkApi.getMutualConnections(username),
    enabled: Boolean(username),
  });
  if (!data?.count) return null;
  return (
    <p className="mt-0.5 text-xs text-muted-foreground">
      {data.count} mutual {data.count === 1 ? "connection" : "connections"}
    </p>
  );
}

export function ConnectionRequests({
  limit = 2,
  className,
  id = "connection-requests",
}: ConnectionRequestsProps) {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["network-requests-received"],
    queryFn: networkApi.getReceivedRequests,
  });

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["network-requests-received"] }),
      queryClient.invalidateQueries({ queryKey: ["network-summary"] }),
      queryClient.invalidateQueries({ queryKey: ["network-connections"] }),
    ]);
  }

  if (isLoading) {
    return (
      <section id={id} className={cn("space-y-3", className)}>
        <h2 className="text-lg font-semibold tracking-tight">Connection requests</h2>
        <div className="flex justify-center py-8">
          <Loader label="Loading requests" />
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section id={id} className={cn("space-y-3", className)}>
        <h2 className="text-lg font-semibold tracking-tight">Connection requests</h2>
        <p className="text-sm text-destructive">
          {getApiErrorMessage(error, "Could not load requests")}
        </p>
      </section>
    );
  }

  const requests = data || [];
  const visible = requests.slice(0, limit);

  return (
    <section id={id} className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold tracking-tight">Connection requests</h2>
        {requests.length > limit ? (
          <Link
            href="/network/requests"
            className="text-sm font-medium text-primary hover:underline"
          >
            Show all →
          </Link>
        ) : null}
      </div>

      {!visible.length ? (
        <p className="rounded-xl border border-dashed border-border/70 bg-card/50 px-4 py-8 text-center text-sm text-muted-foreground">
          No pending connection requests.
        </p>
      ) : (
        <ul className="space-y-2">
          {visible.map((req) => (
            <li
              key={req.id}
              className="flex items-center gap-3 rounded-xl border border-border/70 bg-card px-3 py-3 shadow-sm"
            >
              <ProfileAvatar
                name={req.user.name}
                username={req.user.username}
                src={req.user.avatar}
                size="md"
                href={`/u/${req.user.username}`}
              />
              <div className="min-w-0 flex-1">
                <Link
                  href={`/u/${req.user.username}`}
                  className="block truncate font-semibold hover:underline"
                >
                  {req.user.name}
                </Link>
                {req.user.headline ? (
                  <p className="truncate text-sm text-muted-foreground">
                    {req.user.headline}
                  </p>
                ) : (
                  <p className="truncate text-sm text-muted-foreground">
                    @{req.user.username}
                  </p>
                )}
                <MutualCount username={req.user.username} />
              </div>
              <div className="flex shrink-0 gap-1.5">
                <button
                  type="button"
                  aria-label={`Reject ${req.user.name}`}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  onClick={async () => {
                    try {
                      await networkApi.rejectRequest(req.id);
                      toast.success("Request declined");
                      await refresh();
                    } catch (err) {
                      toast.error(getApiErrorMessage(err));
                    }
                  }}
                >
                  <X className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  aria-label={`Accept ${req.user.name}`}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90"
                  onClick={async () => {
                    try {
                      await networkApi.acceptRequest(req.id);
                      toast.success("Connection accepted");
                      await refresh();
                    } catch (err) {
                      toast.error(getApiErrorMessage(err));
                    }
                  }}
                >
                  <Check className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
