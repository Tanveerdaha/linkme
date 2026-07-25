"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Feed } from "@/components/feed/Feed";
import { BottomNav } from "@/components/layout/bottom-nav";
import { SiteHeader } from "@/components/layout/site-header";
import { AboutSection } from "@/components/profile/AboutSection";
import { ActivityTimeline } from "@/components/profile/ActivityTimeline";
import { MediaGallery } from "@/components/profile/MediaGallery";
import { ProfileHeader } from "@/components/profile/ProfileHeader";
import { ProfileTabs, type ProfileTab } from "@/components/profile/ProfileTabs";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getPublicProfile } from "@/services/profile";
import { useAuthStore } from "@/stores/authStore";

export default function PublicProfilePage() {
  const params = useParams<{ username: string }>();
  const username = params.username;
  const [tab, setTab] = useState<ProfileTab>("posts");
  const authUser = useAuthStore((s) => s.user);
  const isOwner = Boolean(authUser && authUser.username === username);

  const { data, isLoading, error } = useQuery({
    queryKey: ["profile", username],
    queryFn: () => getPublicProfile(username),
    enabled: Boolean(username),
  });

  return (
    <div className="relative isolate min-h-screen pb-16 md:pb-0">
      <SiteHeader />
      {isLoading ? (
        <main className="relative z-[1] mx-auto flex w-full max-w-3xl justify-center px-4 py-16">
          <Loader label="Loading profile" />
        </main>
      ) : error || !data ? (
        <main className="relative z-[1] mx-auto w-full max-w-3xl px-4 py-16">
          <p className="text-sm text-destructive">
            {getApiErrorMessage(error, "Profile not found")}
          </p>
        </main>
      ) : (
        <main className="page-container relative z-[1] mx-auto w-full max-w-3xl space-y-5 px-4 py-8 sm:py-10">
          <ProfileHeader profile={data} editable={isOwner} />
          <ProfileTabs value={tab} onChange={setTab} />
          {tab === "about" ? <AboutSection profile={data} /> : null}
          {tab === "posts" ? (
            <div className="rounded-2xl border border-border/70 bg-card px-2 sm:px-3">
              <Feed
                mode="author"
                username={username}
                emptyMessage={
                  data.is_private
                    ? "This profile is private."
                    : `@${username} hasn't shared any public posts yet.`
                }
              />
            </div>
          ) : null}
          {tab === "media" ? <MediaGallery username={username} /> : null}
          {tab === "activity" ? <ActivityTimeline username={username} /> : null}
        </main>
      )}
      <BottomNav />
    </div>
  );
}
