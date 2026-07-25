"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { beginGoogleOAuthRedirect, getGoogleClientId } from "@/lib/googleOAuth";
import { cn } from "@/lib/utils";

type GoogleLoginButtonProps = {
  className?: string;
  label?: string;
};

function GoogleMark({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 10.2v3.6h5.1c-.2 1.2-.9 2.3-1.9 3l3.1 2.4c1.8-1.7 2.9-4.1 2.9-7 0-.7-.1-1.3-.2-1.9H12z"
      />
      <path
        fill="#34A853"
        d="M5.3 14.3l-.8.6-2.5 1.9C3.5 20.1 7.4 23 12 23c2.7 0 5-.9 6.7-2.4l-3.1-2.4c-.9.6-2.1 1-3.6 1-2.8 0-5.1-1.9-6-4.4z"
      />
      <path
        fill="#4A90E2"
        d="M3.9 7.2A9.9 9.9 0 0 0 2 12c0 1.7.4 3.3 1.1 4.7l3.3-2.6c-.3-.8-.5-1.6-.5-2.1 0-.8.2-1.6.5-2.3L3.9 7.2z"
      />
      <path
        fill="#FBBC05"
        d="M12 4.8c1.5 0 2.9.5 4 1.5l2.9-2.9C16.9 1.7 14.7.8 12 .8 7.4.8 3.5 3.7 1.9 8.1l3.4 2.6C6.9 6.7 9.2 4.8 12 4.8z"
      />
    </svg>
  );
}

export function GoogleLoginButton({
  className,
  label = "Continue with Google",
}: GoogleLoginButtonProps) {
  const [busy, setBusy] = useState(false);
  const configured = Boolean(getGoogleClientId());

  function handleClick() {
    if (!configured) {
      toast.error("Google sign-in is not configured yet. Add NEXT_PUBLIC_GOOGLE_CLIENT_ID.");
      return;
    }
    setBusy(true);
    try {
      beginGoogleOAuthRedirect();
    } catch {
      setBusy(false);
      toast.error("Unable to continue with Google. Please try again.");
    }
  }

  return (
    <Button
      type="button"
      variant="outline"
      className={cn("w-full gap-2", className)}
      disabled={busy}
      onClick={handleClick}
    >
      <GoogleMark className="h-4 w-4" />
      {busy ? "Redirecting…" : label}
    </Button>
  );
}

export function AuthDivider({ label = "OR" }: { label?: string }) {
  return (
    <div className="relative my-1 flex items-center gap-3 py-1">
      <div className="h-px flex-1 bg-border" />
      <span className="text-xs font-medium tracking-wide text-muted-foreground">{label}</span>
      <div className="h-px flex-1 bg-border" />
    </div>
  );
}
