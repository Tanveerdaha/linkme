"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Feed } from "@/components/feed/Feed";
import { BottomNav } from "@/components/layout/bottom-nav";
import { MiniProfileCard } from "@/components/profile/MiniProfileCard";
import { Button } from "@/components/ui/button";
import { getMeProfile } from "@/services/profile";
import { getNetworkSummary } from "@/services/network";

export default function HomeFeedPage() {
  const { data: profile } = useQuery({
    queryKey: ["profile", "me"],
    queryFn: getMeProfile,
  });

  const { data: network } = useQuery({
    queryKey: ["network-summary"],
    queryFn: getNetworkSummary,
  });

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-6 pb-20 md:pb-8">
      <div className="flex justify-center gap-6 lg:justify-start">
        {/* Left sidebar — desktop only */}
        <div className="hidden w-[260px] shrink-0 md:block">
          <div className="sticky top-20">
            {profile ? (
              <MiniProfileCard
                user={{
                  name: profile.name,
                  username: profile.username,
                  avatar: profile.avatar,
                }}
                connectionsCount={network?.connections ?? 0}
                postsCount={profile.statistics?.posts ?? 0}
              />
            ) : (
              <div
                className="h-52 animate-pulse rounded-xl border border-border/70 bg-card/70"
                aria-hidden
              />
            )}
          </div>
        </div>

        {/* Center feed */}
        <div className="w-full max-w-[650px] min-w-0 flex-1">
          <div className="mb-4 hidden justify-end md:flex">
            <Button asChild>
              <Link href="/create">Create post</Link>
            </Button>
          </div>

          <div className="rounded-2xl border border-border/70 bg-card/70 px-2 sm:px-3">
            <Feed
              mode="user"
              emptyMessage="Your feed is empty. Create a post to get started."
            />
          </div>
        </div>

        {/* Right spacer for LinkedIn-style balance on wide screens */}
        <div className="hidden w-[260px] shrink-0 xl:block" aria-hidden />
      </div>

      <BottomNav active="/home" />
    </main>
  );
}
