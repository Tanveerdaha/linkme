"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { BottomNav } from "@/components/layout/bottom-nav";
import { ConnectionRequestCard } from "@/components/network/ConnectionRequestCard";
import { Loader } from "@/components/ui/loader";
import { cn } from "@/lib/utils";
import { getApiErrorMessage } from "@/services/api";
import * as networkApi from "@/services/network";

type Tab = "received" | "sent";

export default function RequestsPage() {
  const [tab, setTab] = useState<Tab>("received");
  const queryClient = useQueryClient();

  const receivedQuery = useQuery({
    queryKey: ["network-requests-received"],
    queryFn: networkApi.getReceivedRequests,
  });
  const sentQuery = useQuery({
    queryKey: ["network-requests-sent"],
    queryFn: networkApi.getSentRequests,
  });

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["network-requests-received"] }),
      queryClient.invalidateQueries({ queryKey: ["network-requests-sent"] }),
      queryClient.invalidateQueries({ queryKey: ["network-summary"] }),
    ]);
  }

  const loading =
    (tab === "received" && receivedQuery.isLoading) ||
    (tab === "sent" && sentQuery.isLoading);

  return (
    <>
      <main className="mx-auto w-full max-w-2xl space-y-5 px-4 py-8 pb-20 md:pb-10">
        <div className="flex items-center justify-between gap-3">
          <h1 className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold">
            Requests
          </h1>
          <Link href="/network" className="text-sm text-primary hover:underline">
            Back
          </Link>
        </div>

        <div className="flex gap-1 border-b border-border/70">
          {(
            [
              ["received", `Received (${receivedQuery.data?.length ?? 0})`],
              ["sent", `Sent (${sentQuery.data?.length ?? 0})`],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={cn(
                "px-4 py-2.5 text-sm font-medium text-muted-foreground",
                tab === key && "border-b-2 border-primary text-foreground",
              )}
            >
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader label="Loading requests" />
          </div>
        ) : tab === "received" ? (
          <ul className="space-y-2">
            {(receivedQuery.data || []).map((req) => (
              <li key={req.id}>
                <ConnectionRequestCard
                  request={req}
                  direction="received"
                  onAccept={async (id) => {
                    try {
                      await networkApi.acceptRequest(id);
                      toast.success("Connection accepted");
                      await refresh();
                    } catch (err) {
                      toast.error(getApiErrorMessage(err));
                    }
                  }}
                  onReject={async (id) => {
                    try {
                      await networkApi.rejectRequest(id);
                      toast.success("Request ignored");
                      await refresh();
                    } catch (err) {
                      toast.error(getApiErrorMessage(err));
                    }
                  }}
                />
              </li>
            ))}
            {!receivedQuery.data?.length ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No pending invitations.
              </p>
            ) : null}
          </ul>
        ) : (
          <ul className="space-y-2">
            {(sentQuery.data || []).map((req) => (
              <li key={req.id}>
                <ConnectionRequestCard
                  request={req}
                  direction="sent"
                  onCancel={async (id) => {
                    try {
                      await networkApi.cancelRequest(id);
                      toast.success("Request cancelled");
                      await refresh();
                    } catch (err) {
                      toast.error(getApiErrorMessage(err));
                    }
                  }}
                />
              </li>
            ))}
            {!sentQuery.data?.length ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No sent requests.
              </p>
            ) : null}
          </ul>
        )}
      </main>
      <BottomNav active="/network" />
    </>
  );
}
