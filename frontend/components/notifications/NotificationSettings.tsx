"use client";

import { useEffect } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import { useNotificationStore } from "@/stores/notificationStore";
import type { NotificationPreferences } from "@/types/notifications";

const labels: { key: keyof NotificationPreferences; label: string; hint: string }[] = [
  {
    key: "post_reactions_enabled",
    label: "Post reactions",
    hint: "When someone reacts to your posts",
  },
  {
    key: "comments_enabled",
    label: "Comments & replies",
    hint: "Comments on your posts and replies to your comments",
  },
  {
    key: "connection_enabled",
    label: "Connections",
    hint: "Connection requests and acceptances",
  },
  {
    key: "messages_enabled",
    label: "Messages",
    hint: "New direct messages when you are away from chat",
  },
];

export function NotificationSettings() {
  const preferences = useNotificationStore((s) => s.preferences);
  const loadPreferences = useNotificationStore((s) => s.loadPreferences);
  const updatePreferences = useNotificationStore((s) => s.updatePreferences);

  useEffect(() => {
    void loadPreferences().catch(() => undefined);
  }, [loadPreferences]);

  if (!preferences) {
    return (
      <p className="text-sm text-muted-foreground">Loading preferences…</p>
    );
  }

  return (
    <div className="space-y-3">
      {labels.map((item) => {
        const enabled = preferences[item.key];
        return (
          <div
            key={item.key}
            className="flex items-center justify-between gap-4 rounded-xl border border-border/60 px-4 py-3"
          >
            <div>
              <p className="text-sm font-medium">{item.label}</p>
              <p className="text-xs text-muted-foreground">{item.hint}</p>
            </div>
            <Button
              type="button"
              variant={enabled ? "default" : "outline"}
              size="sm"
              onClick={() => {
                void updatePreferences({ [item.key]: !enabled })
                  .then(() => toast.success("Preferences updated"))
                  .catch((err) =>
                    toast.error(getApiErrorMessage(err, "Could not update")),
                  );
              }}
            >
              {enabled ? "On" : "Off"}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
