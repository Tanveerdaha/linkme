"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader } from "@/components/ui/loader";
import { consumeGoogleOAuthState } from "@/lib/googleOAuth";
import { getApiErrorMessage } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

function GoogleCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const loginWithGoogle = useAuthStore((s) => s.loginWithGoogle);
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const oauthError = searchParams.get("error");
    if (oauthError) {
      const message =
        oauthError === "access_denied"
          ? "Google sign-in was cancelled."
          : "Unable to continue with Google. Please try again.";
      setError(message);
      toast.error(message);
      return;
    }

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    if (!code) {
      setError("Missing Google authorization code.");
      return;
    }
    if (!consumeGoogleOAuthState(state)) {
      setError("Invalid Google sign-in session. Please try again.");
      return;
    }

    void (async () => {
      try {
        await loginWithGoogle({ code });
        toast.success("Welcome");
        router.replace("/home");
      } catch (err) {
        const message = getApiErrorMessage(
          err,
          "Unable to continue with Google. Please try again.",
        );
        setError(message);
        toast.error(message);
      }
    })();
  }, [loginWithGoogle, router, searchParams]);

  return (
    <Card className="w-full border-border/80 bg-card/90 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="font-[family-name:var(--font-fraunces)] text-2xl">
          {error ? "Sign-in failed" : "Signing you in"}
        </CardTitle>
        <CardDescription>
          {error
            ? "We could not complete Google authentication."
            : "Finishing Google sign-in with LinkMe…"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error ? (
          <>
            <p className="text-sm text-destructive">{error}</p>
            <Button asChild className="w-full">
              <Link href="/login">Back to login</Link>
            </Button>
          </>
        ) : (
          <div className="flex justify-center py-6">
            <Loader />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function GoogleCallbackPage() {
  return (
    <main className="mx-auto flex min-h-[calc(100vh-3.5rem)] w-full max-w-md items-center px-4 py-10">
      <Suspense
        fallback={
          <Card className="w-full border-border/80 bg-card/90">
            <CardContent className="flex justify-center py-16">
              <Loader />
            </CardContent>
          </Card>
        }
      >
        <GoogleCallbackInner />
      </Suspense>
    </main>
  );
}
