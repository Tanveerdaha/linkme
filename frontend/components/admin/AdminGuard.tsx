"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Loader } from "@/components/ui/loader";
import { useAuthStore } from "@/stores/authStore";
import { useAdminStore } from "@/stores/adminStore";
import { getApiErrorMessage } from "@/services/api";

type AdminGuardProps = {
  children: React.ReactNode;
};

export function AdminGuard({ children }: AdminGuardProps) {
  const router = useRouter();
  const hasHydrated = useAuthStore((s) => s._hasHydrated);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const loadMe = useAdminStore((s) => s.loadMe);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasHydrated) return;
    if (!isAuthenticated) {
      router.replace("/login?next=/admin");
      return;
    }
    let cancelled = false;
    loadMe()
      .then(() => {
        if (!cancelled) setReady(true);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(getApiErrorMessage(err, "Admin access denied"));
        router.replace("/settings");
      });
    return () => {
      cancelled = true;
    };
  }, [hasHydrated, isAuthenticated, loadMe, router]);

  if (!hasHydrated || !ready) {
    return (
      <div className="flex min-h-screen items-center justify-center gap-2 text-sm text-muted-foreground">
        <Loader className="h-4 w-4" />
        {error || "Verifying admin access…"}
      </div>
    );
  }

  return <>{children}</>;
}
