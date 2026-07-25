"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Feed } from "@/components/feed/Feed";
import { BottomNav } from "@/components/layout/bottom-nav";
import { AboutSection } from "@/components/profile/AboutSection";
import { ActivityTimeline } from "@/components/profile/ActivityTimeline";
import { MediaGallery } from "@/components/profile/MediaGallery";
import { ProfileCompletionBanner } from "@/components/profile/ProfileCompletion";
import { ProfileHeader } from "@/components/profile/ProfileHeader";
import { ProfileTabs, type ProfileTab } from "@/components/profile/ProfileTabs";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getMeProfile } from "@/services/profile";

export default function ProfilePage() {
  const [tab, setTab] = useState<ProfileTab>("posts");
  const { data, isLoading, error } = useQuery({
    queryKey: ["profile", "me"],
    queryFn: getMeProfile,
  });

  if (isLoading) {
    return (
      <main className="relative z-[1] mx-auto flex w-full max-w-3xl justify-center px-4 py-16">
        <Loader label="Loading profile" />
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="relative z-[1] mx-auto w-full max-w-3xl px-4 py-16">
        <p className="text-sm text-destructive">
          {getApiErrorMessage(error, "Could not load profile")}
        </p>
      </main>
    );
  }

  return (
    <>
      <main className="page-container relative z-[1] mx-auto w-full max-w-3xl space-y-5 px-4 py-8 pb-20 sm:py-10 md:pb-10">
        <ProfileHeader profile={data} editable />
        <ProfileCompletionBanner completion={data.completion} />
        <ProfileTabs value={tab} onChange={setTab} />
        {tab === "about" ? <AboutSection profile={data} /> : null}
        {tab === "posts" ? (
          <div className="rounded-2xl border border-border/70 bg-card px-2 sm:px-3">
            <Feed
              mode="author"
              username={data.username}
              emptyMessage="You haven't posted yet. Share your first update."
            />
          </div>
        ) : null}
        {tab === "media" ? <MediaGallery username={data.username} /> : null}
        {tab === "activity" ? (
          <ActivityTimeline username={data.username} />
        ) : null}
      </main>
      <BottomNav active="/profile" />
    </>
  );
}
