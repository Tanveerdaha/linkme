"use client";

import { VisibilitySelector } from "@/components/privacy/VisibilitySelector";
import type { MessagePermission } from "@/types/moderation";

type MessagePermissionProps = {
  value: MessagePermission;
  onChange: (value: MessagePermission) => void;
  disabled?: boolean;
};

export function MessagePermissionControl({
  value,
  onChange,
  disabled,
}: MessagePermissionProps) {
  return (
    <VisibilitySelector
      label="Who can message you?"
      value={value}
      disabled={disabled}
      onChange={onChange}
      options={[
        {
          value: "CONNECTIONS_ONLY",
          label: "Connections",
          description: "Only people you're connected with can send messages.",
        },
        {
          value: "NOBODY",
          label: "Nobody",
          description: "Disable incoming direct messages.",
        },
      ]}
    />
  );
}
