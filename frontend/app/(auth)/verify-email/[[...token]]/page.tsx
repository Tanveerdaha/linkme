"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { verifyEmail } from "@/services/auth";

function VerifyEmailInner() {
  const params = useParams<{ token?: string | string[] }>();
  const searchParams = useSearchParams();
  const emailHint = searchParams.get("email");

  const rawToken = params?.token;
  const token = Array.isArray(rawToken) ? rawToken.join("/") : rawToken;

  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    token ? "loading" : "idle",
  );
  const [message, setMessage] = useState(
    emailHint
      ? `We sent a verification link to ${emailHint}. Check your inbox.`
      : "Open the verification link from your email to activate your account.",
  );

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const decoded = decodeURIComponent(token);
        const result = await verifyEmail(decoded);
        if (!cancelled) {
          setStatus("success");
          setMessage(result.message);
        }
      } catch (error) {
        if (!cancelled) {
          setStatus("error");
          setMessage(getApiErrorMessage(error, "Verification failed"));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3.5rem)] w-full max-w-md items-center px-4 py-10">
      <Card className="w-full animate-fade-up">
        <CardHeader>
          <CardTitle className="font-[family-name:var(--font-fraunces)] text-2xl">
            Verify email
          </CardTitle>
          <CardDescription>
            {status === "loading" ? "Confirming your email…" : "Account activation"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {status === "loading" ? <Loader label="Verifying" /> : <p className="text-sm text-muted-foreground">{message}</p>}
          {status === "success" && (
            <Button asChild className="w-full">
              <Link href="/login">Continue to login</Link>
            </Button>
          )}
          {status === "error" && (
            <Button asChild variant="outline" className="w-full">
              <Link href="/signup">Back to signup</Link>
            </Button>
          )}
          {status === "idle" && (
            <Button asChild variant="outline" className="w-full">
              <Link href="/login">Go to login</Link>
            </Button>
          )}
        </CardContent>
      </Card>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[50vh] items-center justify-center">
          <Loader />
        </div>
      }
    >
      <VerifyEmailInner />
    </Suspense>
  );
}
