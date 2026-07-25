"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Legacy route — privacy settings now live in the Settings center.
 */
export default function PrivacySettingsRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/settings?section=privacy");
  }, [router]);
  return null;
}
