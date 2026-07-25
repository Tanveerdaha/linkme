"use client";

import Link from "next/link";
import { Globe, MapPin, Settings } from "lucide-react";

import { ConnectionButton, ConnectLoginPrompt } from "@/components/network/ConnectionButton";
import { MessageButton } from "@/components/messaging/MessageButton";
import { SafetyMenu } from "@/components/moderation/SafetyMenu";
import { MutualConnections } from "@/components/network/MutualConnections";
import { CoverImage } from "@/components/profile/CoverImage";
import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { ProfileStats } from "@/components/profile/ProfileStats";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";
import type { MeProfile, PublicProfile } from "@/types";

type ProfileHeaderProps = {
  profile: MeProfile | PublicProfile;
  editable?: boolean;
};

function isMeProfile(profile: MeProfile | PublicProfile): profile is MeProfile {
  return "email" in profile;
}

export function ProfileHeader({ profile, editable = false }: ProfileHeaderProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const stats = profile.statistics;
  const pronouns = isMeProfile(profile)
    ? profile.pronouns
    : profile.pronouns || "";
  const isPrivate = "is_private" in profile && profile.is_private;

  return (
    <section className="animate-fade-up relative z-[1] overflow-hidden rounded-2xl border border-border/70 bg-card">
      <div className="relative">
        <CoverImage src={profile.cover_image} />
        {editable ? (
          <Link
            href="/settings"
            aria-label="Settings"
            className="absolute right-3 top-3 z-10 inline-flex h-9 w-9 items-center justify-center rounded-full border border-border/60 bg-card/95 text-foreground shadow-sm backdrop-blur-sm transition-colors hover:bg-card md:hidden"
          >
            <Settings className="h-4 w-4" />
          </Link>
        ) : null}
      </div>
      <div className="relative px-5 pb-6 pt-0 sm:px-8">
        <div className="-mt-12 flex flex-col gap-4 sm:-mt-14 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex items-end gap-4">
            <ProfileAvatar
              name={profile.name}
              username={profile.username}
              src={profile.avatar}
              size="xl"
            />
            <div className="pb-1">
              <h1 className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold tracking-tight sm:text-3xl">
                {profile.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                @{profile.username}
                {pronouns ? (
                  <span className="text-muted-foreground/80"> · {pronouns}</span>
                ) : null}
              </p>
              {profile.headline && !isPrivate ? (
                <p className="mt-1 text-sm text-foreground/80">{profile.headline}</p>
              ) : null}
            </div>
          </div>

          <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
            {editable ? (
              <Button asChild variant="outline" className="w-full sm:w-auto">
                <Link href="/profile/edit">Edit profile</Link>
              </Button>
            ) : isAuthenticated ? (
              <>
                <ConnectionButton
                  username={profile.username}
                  className="w-full sm:w-auto"
                />
                <MessageButton
                  username={profile.username}
                  className="w-full sm:w-auto"
                />
                {profile.id ? (
                  <SafetyMenu
                    contentType="USER"
                    objectId={String(profile.id)}
                    username={profile.username}
                    label={`@${profile.username}`}
                    showBlock
                  />
                ) : null}
              </>
            ) : (
              <ConnectLoginPrompt className="w-full sm:w-auto" />
            )}
          </div>
        </div>

        {isPrivate ? (
          <p className="mt-5 text-sm text-muted-foreground">
            This profile is private. Limited information is visible.
          </p>
        ) : (
          <>
            {!editable && profile.bio ? (
              <p className="mt-5 max-w-2xl text-sm leading-relaxed text-foreground/85">
                {profile.bio}
              </p>
            ) : null}
            <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
              {profile.location ? (
                <span className="inline-flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5" />
                  {profile.location}
                </span>
              ) : null}
              {profile.website ? (
                <a
                  href={profile.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-primary hover:underline"
                >
                  <Globe className="h-3.5 w-3.5" />
                  {profile.website.replace(/^https?:\/\//, "")}
                </a>
              ) : null}
            </div>
            <ProfileStats statistics={stats} className="mt-4" />
            {!editable && isAuthenticated ? (
              <div className="mt-4">
                <MutualConnections username={profile.username} />
              </div>
            ) : null}
          </>
        )}
      </div>
    </section>
  );
}
