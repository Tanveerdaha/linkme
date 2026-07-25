"use client";

import { cn } from "@/lib/utils";

type StatsCardProps = {
  label: string;
  value: number | string;
  hint?: string;
  className?: string;
};

export function StatsCard({ label, value, hint, className }: StatsCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border/60 bg-card/80 px-4 py-4 animate-fade-up",
        className,
      )}
    >
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-2 font-[family-name:var(--font-fraunces)] text-3xl font-semibold tabular-nums">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
