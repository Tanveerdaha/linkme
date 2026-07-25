"use client";

import { useAdminStore } from "@/stores/adminStore";
import { useAuthStore } from "@/stores/authStore";

type AdminHeaderProps = {
  title: string;
  description?: string;
};

export function AdminHeader({ title, description }: AdminHeaderProps) {
  const me = useAdminStore((s) => s.me);
  const user = useAuthStore((s) => s.user);

  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-3 border-b border-border/60 pb-4">
      <div>
        <h1 className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold tracking-tight">
          {title}
        </h1>
        {description ? (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      <div className="text-right text-sm">
        <p className="font-medium">{me?.username || user?.username}</p>
        <p className="text-xs text-muted-foreground">{me?.role || "ADMIN"}</p>
      </div>
    </header>
  );
}
