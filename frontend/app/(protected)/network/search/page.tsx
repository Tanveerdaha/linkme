"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { BottomNav } from "@/components/layout/bottom-nav";
import { ConnectionButton } from "@/components/network/ConnectionButton";
import { NetworkCard } from "@/components/network/NetworkCard";
import { SearchBar } from "@/components/search/SearchBar";
import { Input } from "@/components/ui/input";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { searchUsers } from "@/services/search";

export default function NetworkSearchPage() {
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [interest, setInterest] = useState("");

  const handleSearch = useCallback((q: string) => {
    setQuery(q);
  }, []);

  const enabled = Boolean(query || location.trim() || interest.trim());
  const { data, isFetching, error } = useQuery({
    queryKey: ["network-search", query, location, interest],
    queryFn: () =>
      searchUsers({
        q: query || undefined,
        location: location.trim() || undefined,
        interest: interest.trim() || undefined,
      }),
    enabled,
  });

  return (
    <>
      <main className="mx-auto w-full max-w-2xl space-y-5 px-4 py-8 pb-20 md:pb-10">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold">
              Search network
            </h1>
            <p className="text-sm text-muted-foreground">
              Find people by name, location, or interest.
            </p>
          </div>
          <Link href="/network" className="text-sm text-primary hover:underline">
            Back
          </Link>
        </div>

        <SearchBar onSearch={handleSearch} autoFocus />
        <div className="grid gap-3 sm:grid-cols-2">
          <Input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Location"
            aria-label="Location filter"
          />
          <Input
            value={interest}
            onChange={(e) => setInterest(e.target.value)}
            placeholder="Interest"
            aria-label="Interest filter"
          />
        </div>

        {error ? (
          <p className="text-sm text-destructive">
            {getApiErrorMessage(error, "Search failed")}
          </p>
        ) : null}

        {!enabled ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            Start typing to find people.
          </p>
        ) : isFetching ? (
          <div className="flex justify-center py-12">
            <Loader label="Searching" />
          </div>
        ) : (
          <ul className="space-y-2">
            {(data?.results || []).map((user) => (
              <li key={user.username}>
                <NetworkCard
                  user={user}
                  actions={<ConnectionButton username={user.username} size="sm" />}
                />
              </li>
            ))}
            {!data?.results?.length ? (
              <p className="py-10 text-center text-sm text-muted-foreground">
                No people found.
              </p>
            ) : null}
          </ul>
        )}
      </main>
      <BottomNav active="/network" />
    </>
  );
}
