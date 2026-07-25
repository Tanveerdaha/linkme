"use client";

import { cn } from "@/lib/utils";

type SettingsSectionProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
};

export function SettingsSection({
  title,
  description,
  children,
  className,
}: SettingsSectionProps) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-border/70 bg-card p-5 shadow-sm sm:p-6",
        className,
      )}
    >
      <div className="mb-5 border-b border-border/60 pb-4">
        <h2 className="font-[family-name:var(--font-fraunces)] text-xl font-semibold tracking-tight">
          {title}
        </h2>
        {description ? (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {children}
    </section>
  );
}
