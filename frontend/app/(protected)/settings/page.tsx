"use client";

import Link from "next/link";
import { Suspense, useEffect } from "react";
import { useSearchParams } from "next/navigation";

import { AccountSettings } from "@/components/settings/AccountSettings";
import { BlockedUsersSettings } from "@/components/settings/BlockedUsersSettings";
import { DangerZone } from "@/components/settings/DangerZone";
import { DataAccountSettings } from "@/components/settings/DataAccountSettings";
import { NotificationSettings } from "@/components/settings/NotificationSettings";
import { PreferenceSettings } from "@/components/settings/PreferenceSettings";
import { PrivacySettings } from "@/components/settings/PrivacySettings";
import { ProfileSettings } from "@/components/settings/ProfileSettings";
import { SecuritySettings } from "@/components/settings/SecuritySettings";
import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { BottomNav } from "@/components/layout/bottom-nav";
import { Loader } from "@/components/ui/loader";
import { useAuthStore } from "@/stores/authStore";
import {
  isSettingsSectionId,
  useSettingsStore,
  type SettingsSectionId,
} from "@/stores/settingsStore";

function ActivePanel({ section }: { section: SettingsSectionId }) {
  switch (section) {
    case "profile":
      return <ProfileSettings />;
    case "account":
      return <AccountSettings />;
    case "privacy":
      return <PrivacySettings />;
    case "blocked":
      return <BlockedUsersSettings />;
    case "security":
      return <SecuritySettings />;
    case "notifications":
      return <NotificationSettings />;
    case "appearance":
      return <PreferenceSettings mode="appearance" />;
    case "language":
      return <PreferenceSettings mode="language" />;
    case "download":
      return <DataAccountSettings mode="download" />;
    case "delete":
      return <DataAccountSettings mode="delete" />;
    default:
      return <ProfileSettings />;
  }
}

function SettingsCenter() {
  const searchParams = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const activeSection = useSettingsStore((s) => s.activeSection);
  const setActiveSection = useSettingsStore((s) => s.setActiveSection);

  useEffect(() => {
    const fromQuery = searchParams.get("section");
    if (isSettingsSectionId(fromQuery)) {
      setActiveSection(fromQuery);
    }
  }, [searchParams, setActiveSection]);

  function handleSelect(section: SettingsSectionId) {
    setActiveSection(section);
    const url = new URL(window.location.href);
    url.searchParams.set("section", section);
    window.history.replaceState({}, "", url.toString());
  }

  return (
    <>
      <main className="mx-auto w-full max-w-6xl px-4 py-8 pb-20 sm:py-10 md:pb-10">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight">
              Settings
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Manage your account, privacy, security and preferences.
            </p>
          </div>
          {user?.is_staff ? (
            <Link
              href="/admin"
              className="text-sm font-medium text-primary hover:underline"
            >
              Admin dashboard
            </Link>
          ) : null}
        </div>

        <SettingsLayout activeSection={activeSection} onSelect={handleSelect}>
          <ActivePanel section={activeSection} />
          <DangerZone />
        </SettingsLayout>
      </main>
      <BottomNav />
    </>
  );
}

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-20">
          <Loader label="Loading settings" />
        </div>
      }
    >
      <SettingsCenter />
    </Suspense>
  );
}
