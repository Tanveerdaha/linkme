"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { SettingsSection } from "@/components/settings/SettingsSection";
import { Input } from "@/components/ui/input";
import { getApiErrorMessage } from "@/services/api";
import * as accountApi from "@/services/account";
import { useAuthStore } from "@/stores/authStore";
import type { AccountStatus } from "@/types/moderation";

export function AccountSettings() {
  const user = useAuthStore((s) => s.user);
  const [status, setStatus] = useState<AccountStatus | null>(null);

  useEffect(() => {
    accountApi
      .getAccountStatus()
      .then(setStatus)
      .catch((err) =>
        toast.error(getApiErrorMessage(err, "Could not load account status")),
      );
  }, []);

  const email = status?.email || user?.email || "";
  const phone = status?.phone_number || user?.phone_number || "";

  return (
    <SettingsSection
      title="Account Information"
      description="Your contact details and account status. Email and phone cannot be edited here."
    >
      <div className="space-y-6">
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Contact info</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1.5 text-sm">
              <span className="font-medium text-muted-foreground">Email</span>
              <Input
                type="email"
                value={email || "Not set"}
                readOnly
                tabIndex={0}
                className="cursor-default bg-muted/40 text-muted-foreground focus-visible:ring-0"
                aria-readonly="true"
              />
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium text-muted-foreground">Phone number</span>
              <Input
                type="tel"
                value={phone || "Not set"}
                readOnly
                tabIndex={0}
                className="cursor-default bg-muted/40 text-muted-foreground focus-visible:ring-0"
                aria-readonly="true"
              />
            </label>
          </div>
        </div>

        <dl className="space-y-4 border-t border-border/60 pt-5 text-sm">
          <div className="grid gap-1 sm:grid-cols-[140px_1fr]">
            <dt className="text-muted-foreground">Username</dt>
            <dd className="font-medium">@{user?.username || "—"}</dd>
          </div>
          <div className="grid gap-1 sm:grid-cols-[140px_1fr]">
            <dt className="text-muted-foreground">Verified</dt>
            <dd className="font-medium">
              {status ? (status.is_verified ? "Yes" : "No") : "…"}
            </dd>
          </div>
          <div className="grid gap-1 sm:grid-cols-[140px_1fr]">
            <dt className="text-muted-foreground">Suspended</dt>
            <dd className="font-medium">
              {status ? (status.is_suspended ? "Yes" : "No") : "…"}
            </dd>
          </div>
          {status?.is_suspended && status.suspension_reason ? (
            <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {status.suspension_reason}
            </p>
          ) : null}
        </dl>
      </div>
    </SettingsSection>
  );
}
