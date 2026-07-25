"use client";

import { cn } from "@/lib/utils";

type ProfileTab = "about" | "posts" | "media" | "activity";

const TABS: { key: ProfileTab; label: string }[] = [
  { key: "about", label: "About" },
  { key: "posts", label: "Posts" },
  { key: "media", label: "Media" },
  { key: "activity", label: "Activity" },
];

type ProfileTabsProps = {
  value: ProfileTab;
  onChange: (tab: ProfileTab) => void;
  className?: string;
};

export type { ProfileTab };

export function ProfileTabs({ value, onChange, className }: ProfileTabsProps) {
  return (
    <div
      className={cn(
        "flex gap-1 overflow-x-auto border-b border-border/70 scrollbar-none",
        className,
      )}
    >
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onChange(tab.key)}
          className={cn(
            "shrink-0 px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors",
            value === tab.key && "border-b-2 border-primary text-foreground",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
