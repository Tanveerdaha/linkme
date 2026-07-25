"use client";

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";

import {
  UsernameInput,
  type UsernameAvailabilityState,
} from "@/components/auth/UsernameInput";
import { AvatarUpload } from "@/components/profile/AvatarUpload";
import { ProfileCompletionBanner } from "@/components/profile/ProfileCompletion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { MeProfile } from "@/types";
import { profileUpdateSchema, type ProfileUpdateFormValues } from "@/types/forms";

type ProfileFormProps = {
  profile: MeProfile;
  onSubmit: (formData: FormData) => Promise<void>;
};

export function ProfileForm({ profile, onSubmit }: ProfileFormProps) {
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [usernameAvailability, setUsernameAvailability] =
    useState<UsernameAvailabilityState>("idle");

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<ProfileUpdateFormValues>({
    resolver: zodResolver(profileUpdateSchema),
    defaultValues: {
      username: profile.username || "",
      first_name: profile.first_name || "",
      last_name: profile.last_name || "",
      bio: profile.bio || "",
      headline: profile.headline || "",
      location: profile.location || "",
      website: profile.website || "",
      interests: profile.interests?.join(", ") || "",
      pronouns: profile.pronouns || "",
      profile_visibility: profile.profile_visibility || "PUBLIC",
      connection_visibility: profile.connection_visibility || "PUBLIC",
    },
  });

  const submit = handleSubmit(async (values) => {
    if (usernameAvailability === "taken" || usernameAvailability === "invalid") {
      return;
    }
    setSubmitting(true);
    try {
      const formData = new FormData();
      if (values.username !== undefined) formData.append("username", values.username);
      if (values.first_name !== undefined) formData.append("first_name", values.first_name);
      if (values.last_name !== undefined) formData.append("last_name", values.last_name);
      if (values.bio !== undefined) formData.append("bio", values.bio);
      if (values.headline !== undefined) formData.append("headline", values.headline);
      if (values.location !== undefined) formData.append("location", values.location);
      if (values.website !== undefined) formData.append("website", values.website);
      if (values.pronouns !== undefined) formData.append("pronouns", values.pronouns);
      if (values.profile_visibility !== undefined) {
        formData.append("profile_visibility", values.profile_visibility);
      }
      if (values.connection_visibility !== undefined) {
        formData.append("connection_visibility", values.connection_visibility);
      }
      if (values.interests !== undefined) {
        const interests = values.interests
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);
        formData.append("interests", JSON.stringify(interests));
      }
      if (avatarFile) formData.append("avatar", avatarFile);
      if (coverFile) formData.append("cover_image", coverFile);
      await onSubmit(formData);
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <form onSubmit={submit} className="space-y-6" noValidate>
      <ProfileCompletionBanner completion={profile.completion} />

      <div className="grid gap-6 sm:grid-cols-2">
        <AvatarUpload
          label="Profile photo"
          currentUrl={profile.avatar}
          onFileChange={setAvatarFile}
          kind="avatar"
        />
        <AvatarUpload
          label="Cover image"
          currentUrl={profile.cover_image}
          onFileChange={setCoverFile}
          kind="cover"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="username" className="text-sm font-medium">
          Username
        </label>
        <Controller
          name="username"
          control={control}
          render={({ field }) => (
            <UsernameInput
              value={field.value || ""}
              onChange={field.onChange}
              error={errors.username?.message}
              currentUsername={profile.username}
              onAvailabilityChange={setUsernameAvailability}
            />
          )}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="first_name" className="text-sm font-medium">
            First name
          </label>
          <Input id="first_name" {...register("first_name")} />
          {errors.first_name && (
            <p className="text-xs text-destructive">{errors.first_name.message}</p>
          )}
        </div>
        <div className="space-y-1.5">
          <label htmlFor="last_name" className="text-sm font-medium">
            Last name
          </label>
          <Input id="last_name" {...register("last_name")} />
          {errors.last_name && (
            <p className="text-xs text-destructive">{errors.last_name.message}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="pronouns" className="text-sm font-medium">
            Pronouns
          </label>
          <Input id="pronouns" placeholder="they/them" {...register("pronouns")} />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="profile_visibility" className="text-sm font-medium">
            Profile visibility
          </label>
          <select
            id="profile_visibility"
            className="flex h-10 w-full rounded-lg border border-input bg-card px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            {...register("profile_visibility")}
          >
            <option value="PUBLIC">Public</option>
            <option value="PRIVATE">Private</option>
          </select>
        </div>
        <div className="space-y-1.5">
          <label htmlFor="connection_visibility" className="text-sm font-medium">
            Who can see your connections
          </label>
          <select
            id="connection_visibility"
            className="flex h-10 w-full rounded-lg border border-input bg-card px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            {...register("connection_visibility")}
          >
            <option value="PUBLIC">Everyone</option>
            <option value="CONNECTIONS_ONLY">Connections only</option>
            <option value="PRIVATE">Only me</option>
          </select>
        </div>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="headline" className="text-sm font-medium">
          Headline
        </label>
        <Input id="headline" placeholder="Software Engineer" {...register("headline")} />
        {errors.headline && (
          <p className="text-xs text-destructive">{errors.headline.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <label htmlFor="bio" className="text-sm font-medium">
          Bio
        </label>
        <textarea
          id="bio"
          rows={4}
          className="flex w-full rounded-lg border border-input bg-card px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          {...register("bio")}
        />
        {errors.bio && <p className="text-xs text-destructive">{errors.bio.message}</p>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <label htmlFor="location" className="text-sm font-medium">
            Location
          </label>
          <Input id="location" {...register("location")} />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="website" className="text-sm font-medium">
            Website
          </label>
          <Input id="website" type="url" placeholder="https://" {...register("website")} />
          {errors.website && (
            <p className="text-xs text-destructive">{errors.website.message}</p>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <label htmlFor="interests" className="text-sm font-medium">
          Interests
        </label>
        <Input
          id="interests"
          placeholder="design, startups, photography"
          {...register("interests")}
        />
        <p className="text-xs text-muted-foreground">Comma-separated list</p>
      </div>

      <Button
        type="submit"
        disabled={
          submitting ||
          usernameAvailability === "checking" ||
          usernameAvailability === "taken" ||
          usernameAvailability === "invalid"
        }
      >
        {submitting ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
