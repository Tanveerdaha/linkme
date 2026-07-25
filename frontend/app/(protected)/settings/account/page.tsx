"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Legacy route — account management now lives in the Settings center.
 */
export default function AccountSettingsRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/settings?section=download");
  }, [router]);
  return null;
}
