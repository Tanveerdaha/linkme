"use client";

import { SettingsSection } from "@/components/settings/SettingsSection";
import { BlockedUsers } from "@/components/privacy/BlockedUsers";

export function BlockedUsersSettings() {
  return (
    <SettingsSection
      title="Blocked Users"
      description="Manage users you have blocked."
    >
      <BlockedUsers />
    </SettingsSection>
  );
}
