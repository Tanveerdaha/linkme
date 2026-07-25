"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import {
  UsernameInput,
  type UsernameAvailabilityState,
} from "@/components/auth/UsernameInput";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { ProfileAvatar } from "@/components/profile/ProfileAvatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getApiErrorMessage } from "@/services/api";
import { getMeProfile, updateMeProfile } from "@/services/profile";

export function ProfileSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [username, setUsername] = useState("");
  const [savedUsername, setSavedUsername] = useState("");
  const [usernameAvailability, setUsernameAvailability] =
    useState<UsernameAvailabilityState>("idle");
  const [avatar, setAvatar] = useState<string | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [headline, setHeadline] = useState("");
  const [bio, setBio] = useState("");

  useEffect(() => {
    getMeProfile()
      .then((profile) => {
        setUsername(profile.username);
        setSavedUsername(profile.username);
        setAvatar(profile.avatar);
        setFirstName(profile.first_name || "");
        setLastName(profile.last_name || "");
        setHeadline(profile.headline || "");
        setBio(profile.bio || "");
      })
      .catch((err) => toast.error(getApiErrorMessage(err, "Could not load profile")))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    if (usernameAvailability === "taken" || usernameAvailability === "invalid") {
      toast.error("Please choose an available username");
      return;
    }
    setSaving(true);
    try {
      const form = new FormData();
      form.append("username", username);
      form.append("first_name", firstName);
      form.append("last_name", lastName);
      form.append("headline", headline);
      form.append("bio", bio);
      const updated = await updateMeProfile(form);
      setAvatar(updated.avatar);
      setUsername(updated.username);
      setSavedUsername(updated.username);
      toast.success("Profile updated");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not save profile"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <SettingsSection title="Edit Profile" description="Loading your profile…">
        <p className="text-sm text-muted-foreground">Please wait…</p>
      </SettingsSection>
    );
  }

  return (
    <SettingsSection
      title="Edit Profile"
      description="Update your profile photo, bio, headline and personal information."
    >
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-4">
          <ProfileAvatar
            name={`${firstName} ${lastName}`.trim() || username}
            username={username}
            src={avatar}
            size="md"
          />
          <div>
            <p className="text-sm font-medium">Profile photo</p>
            <p className="text-xs text-muted-foreground">
              Change your photo from the full profile editor.
            </p>
            <Button asChild variant="outline" size="sm" className="mt-2">
              <Link href="/profile/edit">Change photo</Link>
            </Button>
          </div>
        </div>

        <label className="block space-y-1.5 text-sm">
          <span className="font-medium">Username</span>
          <UsernameInput
            value={username}
            onChange={setUsername}
            currentUsername={savedUsername}
            onAvailabilityChange={setUsernameAvailability}
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-1.5 text-sm">
            <span className="font-medium">First name</span>
            <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </label>
          <label className="space-y-1.5 text-sm">
            <span className="font-medium">Last name</span>
            <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </label>
        </div>

        <label className="block space-y-1.5 text-sm">
          <span className="font-medium">Headline</span>
          <Input
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder="e.g. Product designer"
          />
        </label>

        <label className="block space-y-1.5 text-sm">
          <span className="font-medium">Bio</span>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            className="flex w-full rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="Tell people a bit about yourself"
          />
        </label>

        <div className="flex justify-end">
          <Button
            type="button"
            onClick={() => void handleSave()}
            disabled={
              saving ||
              usernameAvailability === "checking" ||
              usernameAvailability === "taken" ||
              usernameAvailability === "invalid"
            }
          >
            {saving ? "Saving…" : "Save changes"}
          </Button>
        </div>
      </div>
    </SettingsSection>
  );
}
