"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { BottomNav } from "@/components/layout/bottom-nav";
import { ConnectionsList } from "@/components/network/ConnectionsList";
import { Input } from "@/components/ui/input";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getConnections } from "@/services/network";

export default function ConnectionsPage() {
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();
  const { data, isFetching, error } = useQuery({
    queryKey: ["network-connections", search],
    queryFn: () => getConnections({ search: search || undefined }),
  });

  return (
    <>
      <main className="mx-auto w-full max-w-2xl space-y-5 px-4 py-8 pb-20 md:pb-10">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold">
              My Connections
            </h1>
            <p className="text-sm text-muted-foreground">
              {data?.count ?? 0}{" "}
              {(data?.count ?? 0) === 1 ? "connection" : "connections"}
            </p>
          </div>
          <Link href="/network" className="text-sm text-primary hover:underline">
            Back
          </Link>
        </div>

        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search connections…"
          aria-label="Search connections"
        />

        {error ? (
          <p className="text-sm text-destructive">
            {getApiErrorMessage(error, "Could not load connections")}
          </p>
        ) : null}

        {isFetching && !data ? (
          <div className="flex justify-center py-12">
            <Loader label="Loading" />
          </div>
        ) : (
          <ConnectionsList
            connections={data?.results || []}
            onRemoved={() => {
              void queryClient.invalidateQueries({
                queryKey: ["network-connections"],
              });
              void queryClient.invalidateQueries({
                queryKey: ["network-summary"],
              });
            }}
          />
        )}
      </main>
      <BottomNav active="/network" />
    </>
  );
}
