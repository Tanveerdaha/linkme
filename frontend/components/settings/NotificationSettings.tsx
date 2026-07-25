"use client";

import { useEffect } from "react";
import { toast } from "sonner";

import { SettingsSection } from "@/components/settings/SettingsSection";
import { Toggle } from "@/components/ui/toggle";
import { getApiErrorMessage } from "@/services/api";
import { useNotificationStore } from "@/stores/notificationStore";
import type { NotificationPreferences } from "@/types/notifications";

type PrefGroup = {
  title: string;
  items: {
    key: keyof NotificationPreferences;
    label: string;
  }[];
};

const GROUPS: PrefGroup[] = [
  {
    title: "Activity",
    items: [
      { key: "post_reactions_enabled", label: "Someone likes my post" },
      { key: "comments_enabled", label: "Someone comments on my post" },
    ],
  },
  {
    title: "Network",
    items: [
      { key: "connection_enabled", label: "Connection requests & accepted" },
    ],
  },
  {
    title: "Messages",
    items: [{ key: "messages_enabled", label: "New messages" }],
  },
];

export function NotificationSettings() {
  const preferences = useNotificationStore((s) => s.preferences);
  const loadPreferences = useNotificationStore((s) => s.loadPreferences);
  const updatePreferences = useNotificationStore((s) => s.updatePreferences);

  useEffect(() => {
    void loadPreferences().catch(() => undefined);
  }, [loadPreferences]);

  return (
    <SettingsSection
      title="Notification Preferences"
      description="Choose what notifications you receive."
    >
      {!preferences ? (
        <p className="text-sm text-muted-foreground">Loading preferences…</p>
      ) : (
        <div className="space-y-6">
          {GROUPS.map((group) => (
            <div key={group.title}>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {group.title}
              </p>
              <ul className="space-y-2">
                {group.items.map((item) => {
                  const enabled = preferences[item.key];
                  return (
                    <li
                      key={item.key}
                      className="flex items-center justify-between gap-4 rounded-xl border border-border/60 px-4 py-3"
                    >
                      <span className="text-sm font-medium">{item.label}</span>
                      <Toggle
                        checked={enabled}
                        aria-label={item.label}
                        onCheckedChange={(next) => {
                          void updatePreferences({ [item.key]: next })
                            .then(() => toast.success("Preferences updated"))
                            .catch((err) =>
                              toast.error(
                                getApiErrorMessage(err, "Could not update"),
                              ),
                            );
                        }}
                      />
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      )}
    </SettingsSection>
  );
}
