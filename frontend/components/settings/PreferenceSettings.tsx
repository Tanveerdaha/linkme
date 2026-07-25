"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { SettingsSection } from "@/components/settings/SettingsSection";
import { cn } from "@/lib/utils";

const THEMES = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
] as const;

export function PreferenceSettings({
  mode = "appearance",
}: {
  mode?: "appearance" | "language";
}) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (mode === "language") {
    return (
      <SettingsSection
        title="Language"
        description="Choose your preferred language."
      >
        <label className="block space-y-1.5 text-sm">
          <span className="font-medium">Language</span>
          <select
            className="flex h-10 w-full max-w-xs rounded-lg border border-input bg-card px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            defaultValue="en"
            aria-label="Language"
          >
            <option value="en">English</option>
          </select>
          <p className="text-xs text-muted-foreground">More languages coming soon.</p>
        </label>
      </SettingsSection>
    );
  }

  return (
    <SettingsSection
      title="Appearance"
      description="Manage theme and display preferences."
    >
      {!mounted ? (
        <p className="text-sm text-muted-foreground">Loading theme…</p>
      ) : (
        <fieldset className="space-y-2">
          <legend className="mb-1 text-sm font-medium">Theme</legend>
          {THEMES.map((option) => {
            const selected = (theme || "system") === option.value;
            return (
              <label
                key={option.value}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 transition-colors",
                  selected
                    ? "border-primary/40 bg-secondary/50"
                    : "border-border/60 hover:bg-muted/30",
                )}
              >
                <input
                  type="radio"
                  name="theme"
                  value={option.value}
                  checked={selected}
                  onChange={() => setTheme(option.value)}
                  className="h-4 w-4 accent-[var(--primary)]"
                />
                <span className="text-sm font-medium">{option.label}</span>
              </label>
            );
          })}
        </fieldset>
      )}
    </SettingsSection>
  );
}
