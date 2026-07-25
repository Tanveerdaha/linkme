"use client";

import { useEffect, useState, useTransition } from "react";
import { toast } from "sonner";

import { BlockedUsers } from "@/components/privacy/BlockedUsers";
import { MessagePermissionControl } from "@/components/privacy/MessagePermission";
import { VisibilitySelector } from "@/components/privacy/VisibilitySelector";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import { usePrivacyStore } from "@/stores/privacyStore";
import type {
  ConnectionVisibility,
  MessagePermission,
  PostVisibility,
  PrivacySettings,
  ProfileVisibility,
} from "@/types/moderation";

export function PrivacySettings() {
  const settings = usePrivacyStore((s) => s.settings);
  const loadSettings = usePrivacyStore((s) => s.loadSettings);
  const updateSettings = usePrivacyStore((s) => s.updateSettings);
  const [draft, setDraft] = useState<PrivacySettings | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    loadSettings()
      .then(() => undefined)
      .catch(() => toast.error("Could not load privacy settings"));
  }, [loadSettings]);

  useEffect(() => {
    if (settings) setDraft(settings);
  }, [settings]);

  function patch<K extends keyof PrivacySettings>(key: K, value: PrivacySettings[K]) {
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

  if (!draft) {
    return <p className="text-sm text-muted-foreground">Loading privacy settings…</p>;
  }

  return (
    <div className="space-y-8">
      <VisibilitySelector
        label="Profile Visibility"
        value={draft.profile_visibility}
        onChange={(v: ProfileVisibility) => patch("profile_visibility", v)}
        options={[
          { value: "PUBLIC", label: "Everyone", description: "Anyone can view your profile." },
          {
            value: "PRIVATE",
            label: "Private",
            description: "Limited profile information is shown to others.",
          },
        ]}
      />

      <VisibilitySelector
        label="Default post visibility"
        value={draft.post_visibility}
        onChange={(v: PostVisibility) => patch("post_visibility", v)}
        options={[
          { value: "PUBLIC", label: "Everyone" },
          { value: "CONNECTIONS_ONLY", label: "Connections only" },
          { value: "PRIVATE", label: "Only me" },
        ]}
      />

      <VisibilitySelector
        label="Who can see your connections?"
        value={draft.connection_visibility}
        onChange={(v: ConnectionVisibility) => patch("connection_visibility", v)}
        options={[
          { value: "PUBLIC", label: "Everyone" },
          { value: "CONNECTIONS_ONLY", label: "Connections only" },
          { value: "PRIVATE", label: "Only me" },
        ]}
      />

      <MessagePermissionControl
        value={draft.message_permission}
        onChange={(v: MessagePermission) => patch("message_permission", v)}
      />

      <Button onClick={handleSave} disabled={pending}>
        {pending ? "Saving…" : "Save changes"}
      </Button>

      <section className="border-t border-border/60 pt-6">
        <h2 className="mb-3 font-[family-name:var(--font-fraunces)] text-lg font-semibold">
          Blocked users
        </h2>
        <BlockedUsers />
      </section>
    </div>
  );
}
