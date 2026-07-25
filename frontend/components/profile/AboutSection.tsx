"use client";

import { Globe, MapPin } from "lucide-react";

import type { MeProfile, PublicProfile } from "@/types";

type AboutSectionProps = {
  profile: MeProfile | PublicProfile;
};

export function AboutSection({ profile }: AboutSectionProps) {
  if ("is_private" in profile && profile.is_private) {
    return (
      <section className="animate-fade-up rounded-2xl border border-border/70 bg-card px-5 py-8 text-center text-sm text-muted-foreground">
        About details are hidden on private profiles.
      </section>
    );
  }

  const joined =
    "joined_date" in profile
      ? profile.joined_date
      : "created_at" in profile
        ? profile.created_at
        : null;

  return (
    <section className="animate-fade-up space-y-5 rounded-2xl border border-border/70 bg-card px-5 py-5 sm:px-6">
      <div>
        <h2 className="font-[family-name:var(--font-fraunces)] text-xl font-semibold">
          About
        </h2>
        {profile.bio ? (
          <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-foreground/85">
            {profile.bio}
          </p>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">No bio yet.</p>
        )}
      </div>

      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        {profile.location ? (
          <div className="flex items-start gap-2">
            <MapPin className="mt-0.5 h-4 w-4 text-muted-foreground" />
            <div>
              <dt className="text-xs text-muted-foreground">Location</dt>
              <dd>{profile.location}</dd>
            </div>
          </div>
        ) : null}
        {profile.website ? (
          <div className="flex items-start gap-2">
            <Globe className="mt-0.5 h-4 w-4 text-muted-foreground" />
            <div>
              <dt className="text-xs text-muted-foreground">Website</dt>
              <dd>
                <a
                  href={profile.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  {profile.website.replace(/^https?:\/\//, "")}
                </a>
              </dd>
            </div>
          </div>
        ) : null}
        {joined ? (
          <div>
            <dt className="text-xs text-muted-foreground">Joined</dt>
            <dd>
              {new Date(joined).toLocaleDateString(undefined, {
                month: "long",
                year: "numeric",
              })}
            </dd>
          </div>
        ) : null}
      </dl>

      {profile.interests?.length ? (
        <div>
          <h3 className="text-sm font-medium">Interests</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {profile.interests.map((interest) => (
              <span
                key={interest}
                className="rounded-md bg-secondary px-2.5 py-1 text-xs text-secondary-foreground"
              >
                {interest}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
