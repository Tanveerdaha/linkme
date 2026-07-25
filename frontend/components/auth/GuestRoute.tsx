"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Loader } from "@/components/ui/loader";
import { useAuthStore } from "@/stores/authStore";

type GuestRouteProps = {
  children: ReactNode;
};

/** Redirects authenticated users away from auth pages. */
export function GuestRoute({ children }: GuestRouteProps) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);

  useEffect(() => {
    if (hasHydrated && isAuthenticated) {
      router.replace("/home");
    }
  }, [hasHydrated, isAuthenticated, router]);

  if (!hasHydrated) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader />
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader />
      </div>
    );
  }

  return <>{children}</>;
}
