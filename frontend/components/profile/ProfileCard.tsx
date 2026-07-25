"use client";

import type { MeProfile, PublicProfile } from "@/types";

type ProfileCardProps = {
  profile: MeProfile | PublicProfile;
};

export function ProfileCard({ profile }: ProfileCardProps) {
  const joined =
    "joined_date" in profile
      ? new Date(profile.joined_date).toLocaleDateString()
      : "created_at" in profile
        ? new Date(profile.created_at).toLocaleDateString()
        : null;

  const rows = [
    { label: "Location", value: profile.location },
    { label: "Website", value: profile.website },
    {
      label: "Interests",
      value: profile.interests?.length ? profile.interests.join(", ") : "",
    },
    { label: "Joined", value: joined || "" },
  ].filter((row) => row.value);

  return (
    <section className="animate-fade-up space-y-4" style={{ animationDelay: "80ms" }}>
      <h2 className="font-[family-name:var(--font-fraunces)] text-xl font-semibold">About</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">No additional information yet.</p>
      ) : (
        <dl className="grid gap-4 sm:grid-cols-2">
          {rows.map((row) => (
            <div key={row.label}>
              <dt className="text-xs uppercase tracking-wide text-muted-foreground">{row.label}</dt>
              <dd className="mt-1 text-sm">
                {row.label === "Website" ? (
                  <a
                    href={row.value}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:underline"
                  >
                    {row.value}
                  </a>
                ) : (
                  row.value
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
