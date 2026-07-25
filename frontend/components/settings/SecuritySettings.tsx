"use client";

import Link from "next/link";
import { MonitorSmartphone } from "lucide-react";

import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";

export function SecuritySettings() {
  return (
    <SettingsSection
      title="Security"
      description="Manage password and account security."
    >
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/60 px-4 py-3">
          <div>
            <p className="text-sm font-medium">Password</p>
            <p className="text-sm text-muted-foreground">••••••••</p>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link href="/forgot-password">Change password</Link>
          </Button>
        </div>

        <div className="rounded-xl border border-border/60 px-4 py-3">
          <p className="text-sm font-medium">Active sessions</p>
          <div className="mt-3 flex items-start gap-3">
            <span className="rounded-lg bg-secondary p-2 text-secondary-foreground">
              <MonitorSmartphone className="h-4 w-4" />
            </span>
            <div>
              <p className="text-sm font-medium">This browser</p>
              <p className="text-xs text-muted-foreground">
                Current session · Last active recently
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-dashed border-border/70 px-4 py-3">
          <p className="text-sm font-medium">Two-factor authentication</p>
          <p className="mt-1 text-sm text-muted-foreground">Coming soon</p>
        </div>
      </div>
    </SettingsSection>
  );
}
