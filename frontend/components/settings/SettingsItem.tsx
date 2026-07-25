"use client";

import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";

type SettingsItemProps = {
  icon: LucideIcon;
  title: string;
  description: string;
  active?: boolean;
  onClick?: () => void;
  className?: string;
};

export function SettingsItem({
  icon: Icon,
  title,
  description,
  active,
  onClick,
  className,
}: SettingsItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full items-start gap-3 rounded-xl border px-3 py-3 text-left transition-colors",
        active
          ? "border-primary/30 bg-secondary/60"
          : "border-transparent hover:border-border/70 hover:bg-muted/40",
        className,
      )}
    >
      <span
        className={cn(
          "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          active ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
        )}
      >
        <Icon className="h-4 w-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-foreground">{title}</span>
        <span className="mt-0.5 block text-xs leading-relaxed text-muted-foreground">
          {description}
        </span>
      </span>
      <ChevronRight
        className={cn(
          "mt-2 h-4 w-4 shrink-0",
          active ? "text-primary" : "text-muted-foreground",
        )}
      />
    </button>
  );
}
