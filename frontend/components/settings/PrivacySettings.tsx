"use client";

import { useEffect, useState, useTransition } from "react";
import { toast } from "sonner";

import { MessagePermissionControl } from "@/components/privacy/MessagePermission";
import { VisibilitySelector } from "@/components/privacy/VisibilitySelector";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import { usePrivacyStore } from "@/stores/privacyStore";
import type {
  ConnectionVisibility,
  MessagePermission,
  PostVisibility,
  PrivacySettings as PrivacySettingsType,
  ProfileVisibility,
} from "@/types/moderation";

export function PrivacySettings() {
  const settings = usePrivacyStore((s) => s.settings);
  const loadSettings = usePrivacyStore((s) => s.loadSettings);
  const updateSettings = usePrivacyStore((s) => s.updateSettings);
  const [draft, setDraft] = useState<PrivacySettingsType | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    loadSettings().catch(() => toast.error("Could not load privacy settings"));
  }, [loadSettings]);

  useEffect(() => {
    if (settings) setDraft(settings);
  }, [settings]);

  function patch<K extends keyof PrivacySettingsType>(
    key: K,
    value: PrivacySettingsType[K],
  ) {
    setDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function handleSave() {
    if (!draft) return;
    startTransition(async () => {
      try {
        await updateSettings({
          profile_visibility: draft.profile_visibility,
          post_visibility: draft.post_visibility,
          connection_visibility: draft.connection_visibility,
          message_permission: draft.message_permission,
        });
        toast.success("Privacy settings saved");
      } catch (err) {
        toast.error(getApiErrorMessage(err, "Could not save settings"));
      }
    });
  }

  return (
    <SettingsSection
      title="Privacy Settings"
      description="Control who can view your profile, posts and connections."
    >
      {!draft ? (
        <p className="text-sm text-muted-foreground">Loading privacy settings…</p>
      ) : (
        <div className="space-y-8">
          <VisibilitySelector
            label="Profile visibility"
            value={draft.profile_visibility}
            onChange={(v: ProfileVisibility) => patch("profile_visibility", v)}
            options={[
              {
                value: "PUBLIC",
                label: "Everyone",
                description: "Anyone can view your profile.",
              },
              {
                value: "PRIVATE",
                label: "Private",
                description: "Limited profile information is shown to others.",
              },
            ]}
          />

          <VisibilitySelector
            label="Post visibility"
            value={draft.post_visibility}
            onChange={(v: PostVisibility) => patch("post_visibility", v)}
            options={[
              { value: "PUBLIC", label: "Everyone" },
              { value: "CONNECTIONS_ONLY", label: "Connections" },
              { value: "PRIVATE", label: "Only me" },
            ]}
          />

          <VisibilitySelector
            label="Connection visibility"
            value={draft.connection_visibility}
            onChange={(v: ConnectionVisibility) =>
              patch("connection_visibility", v)
            }
            options={[
              { value: "PUBLIC", label: "Everyone" },
              { value: "CONNECTIONS_ONLY", label: "Connections" },
              { value: "PRIVATE", label: "Only me" },
            ]}
          />

          <div>
            <p className="mb-2 text-sm font-medium">Who can message you?</p>
            <MessagePermissionControl
              value={draft.message_permission}
              onChange={(v: MessagePermission) => patch("message_permission", v)}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSave} disabled={pending}>
              {pending ? "Saving…" : "Save changes"}
            </Button>
          </div>
        </div>
      )}
    </SettingsSection>
  );
}
