"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ProfileForm } from "@/components/profile/ProfileForm";
import { Button } from "@/components/ui/button";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getMeProfile, updateMeProfile } from "@/services/profile";

export default function EditProfilePage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["profile", "me"],
    queryFn: getMeProfile,
  });

  if (isLoading) {
    return (
      <main className="mx-auto flex w-full max-w-2xl justify-center px-4 py-16">
        <Loader label="Loading profile" />
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="mx-auto w-full max-w-2xl px-4 py-16">
        <p className="text-sm text-destructive">{getApiErrorMessage(error, "Could not load profile")}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-2xl space-y-6 px-4 py-8 sm:py-10">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold">Edit profile</h1>
          <p className="mt-1 text-sm text-muted-foreground">Update how you appear on LinkMe.</p>
        </div>
        <Button asChild variant="ghost">
          <Link href="/profile">Cancel</Link>
        </Button>
      </div>
      <ProfileForm
        profile={data}
        onSubmit={async (formData) => {
          try {
            await updateMeProfile(formData);
            await queryClient.invalidateQueries({ queryKey: ["profile", "me"] });
            toast.success("Profile updated");
            router.push("/profile");
          } catch (err) {
            toast.error(getApiErrorMessage(err, "Could not save profile"));
            throw err;
          }
        }}
      />
    </main>
  );
}
