"use client";

import { useQuery } from "@tanstack/react-query";

import { BottomNav } from "@/components/layout/bottom-nav";
import { ConnectionRequests } from "@/components/network/ConnectionRequests";
import { ExplorePeople } from "@/components/network/ExplorePeople";
import { NetworkSummaryCards } from "@/components/network/NetworkSummaryCards";
import { PeopleSuggestions } from "@/components/network/PeopleSuggestions";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getNetworkSummary } from "@/services/network";

function scrollToId(id: string) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

export default function NetworkDashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["network-summary"],
    queryFn: getNetworkSummary,
  });

  return (
    <>
      <main className="mx-auto w-full max-w-6xl px-4 py-8 pb-20 sm:py-10 md:pb-10">
        <div className="mb-6">
          <h1 className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight">
            My Network
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Grow your professional circle on LinkMe.
          </p>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader label="Loading network" />
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">
            {getApiErrorMessage(error, "Could not load network")}
          </p>
        ) : (
          <div className="space-y-8">
            <NetworkSummaryCards
              summary={data}
              onViewRequests={() => scrollToId("connection-requests")}
              onViewSuggestions={() => scrollToId("people-suggestions")}
            />
            <ConnectionRequests limit={2} />
            <PeopleSuggestions limit={4} />
            <ExplorePeople limit={6} />
          </div>
        )}
      </main>
      <BottomNav active="/network" />
    </>
  );
}
