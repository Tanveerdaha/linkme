"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";
import { useSettingsStore } from "@/stores/settingsStore";

export function DangerZone() {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const setActiveSection = useSettingsStore((s) => s.setActiveSection);

  return (
    <SettingsSection
      title="Danger Zone"
      description="Sign out or permanently leave LinkMe."
      className="border-destructive/30"
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/60 px-4 py-3">
          <div>
            <p className="text-sm font-medium">Logout</p>
            <p className="text-xs text-muted-foreground">
              Sign out of your account on this device.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={async () => {
              await logout();
              toast.success("Signed out");
              router.push("/login");
            }}
          >
            Log out
          </Button>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3">
          <div>
            <p className="text-sm font-medium text-destructive">Delete account</p>
            <p className="text-xs text-muted-foreground">
              Deactivate or permanently remove your account.
            </p>
          </div>
          <Button
            variant="destructive"
            onClick={() => setActiveSection("delete")}
          >
            Delete Account
          </Button>
        </div>
      </div>
    </SettingsSection>
  );
}
