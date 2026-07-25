"use client";

import Link from "next/link";

import { BottomNav } from "@/components/layout/bottom-nav";
import { NetworkSuggestedUsers } from "@/components/network/SuggestedUsers";

export default function DiscoverPage() {
  return (
    <>
      <main className="mx-auto w-full max-w-2xl space-y-5 px-4 py-8 pb-20 md:pb-10">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold">
              Discover
            </h1>
            <p className="text-sm text-muted-foreground">
              People you may want to connect with.
            </p>
          </div>
          <Link href="/network" className="text-sm text-primary hover:underline">
            Back
          </Link>
        </div>
        <NetworkSuggestedUsers title="Suggestions" />
      </main>
      <BottomNav active="/network" />
    </>
  );
}
