"use client";

import { SettingsSidebar } from "@/components/settings/SettingsSidebar";
import type { SettingsSectionId } from "@/stores/settingsStore";
import { cn } from "@/lib/utils";

type SettingsLayoutProps = {
  activeSection: SettingsSectionId;
  onSelect: (section: SettingsSectionId) => void;
  children: React.ReactNode;
  className?: string;
};

export function SettingsLayout({
  activeSection,
  onSelect,
  children,
  className,
}: SettingsLayoutProps) {
  return (
    <div className={cn("grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]", className)}>
      <aside className="lg:sticky lg:top-20 lg:self-start">
        <div className="rounded-2xl border border-border/70 bg-card/80 p-3 shadow-sm sm:p-4">
          <SettingsSidebar activeSection={activeSection} onSelect={onSelect} />
        </div>
      </aside>
      <div className="min-w-0 space-y-6">{children}</div>
    </div>
  );
}
