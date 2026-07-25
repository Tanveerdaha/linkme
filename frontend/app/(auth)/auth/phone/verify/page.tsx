"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { sendPhoneOtp } from "@/services/auth";
import { useAuthStore } from "@/stores/authStore";
import { phoneOtpSchema, type PhoneOtpFormValues } from "@/types/forms";

function formatCountdown(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function PhoneVerifyInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const loginWithPhone = useAuthStore((s) => s.loginWithPhone);
  const phone = (searchParams.get("phone") || "").trim();
  const initialResend = Number(searchParams.get("resend") || "120");

  const [secondsLeft, setSecondsLeft] = useState(
    Number.isFinite(initialResend) && initialResend > 0 ? Math.floor(initialResend) : 120,
  );
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);

  const canResend = secondsLeft <= 0;

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const id = window.setInterval(() => {
      setSecondsLeft((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => window.clearInterval(id);
  }, [secondsLeft]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PhoneOtpFormValues>({
    resolver: zodResolver(phoneOtpSchema),
    defaultValues: { code: "" },
  });

  const maskedPhone = useMemo(() => {
    if (!phone) return "";
    if (phone.length < 6) return phone;
    return `${phone.slice(0, 3)}••••${phone.slice(-4)}`;
  }, [phone]);

  const onSubmit = handleSubmit(async (values) => {
    if (!phone) {
      toast.error("Missing phone number. Start again.");
      router.replace("/login");
      return;
    }
    setSubmitting(true);
    try {
      await loginWithPhone(phone, values.code.trim());
      toast.success("Welcome");
      router.replace("/home");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Invalid verification code"));
    } finally {
      setSubmitting(false);
    }
  });

  const handleResend = useCallback(async () => {
    if (!canResend || !phone || resending) return;
    setResending(true);
    try {
      const result = await sendPhoneOtp(phone);
      toast.success(result.message || "Code resent");
      setSecondsLeft(result.resend_available_in ?? 120);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to resend code"));
    } finally {
      setResending(false);
    }
  }, [canResend, phone, resending]);

  if (!phone) {
    return (
      <Card className="w-full border-border/80 bg-card/90">
        <CardHeader>
          <CardTitle className="font-[family-name:var(--font-fraunces)] text-2xl">
            Phone verification
          </CardTitle>
          <CardDescription>Start by entering your phone number.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild className="w-full">
            <Link href="/login">Back to login</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full animate-fade-up border-border/80 bg-card/90 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="font-[family-name:var(--font-fraunces)] text-2xl">
          Enter verification code
        </CardTitle>
        <CardDescription>
          We sent a 6-digit WhatsApp code to {maskedPhone}.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <label htmlFor="code" className="text-sm font-medium">
              Verification code
            </label>
            <Input
              id="code"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              placeholder="123456"
              className="tracking-[0.35em]"
              {...register("code")}
            />
            {errors.code && <p className="text-xs text-destructive">{errors.code.message}</p>}
          </div>
          <Button className="w-full" type="submit" disabled={submitting}>
            {submitting ? "Verifying…" : "Verify and continue"}
          </Button>
        </form>

        <div className="text-center text-sm text-muted-foreground">
          {canResend ? (
            <button
              type="button"
              onClick={() => void handleResend()}
              disabled={resending}
              className="font-medium text-primary underline-offset-4 hover:underline disabled:opacity-60"
            >
              {resending ? "Resending…" : "Resend code"}
            </button>
          ) : (
            <p>
              Resend available in{" "}
              <span className="font-medium text-foreground">{formatCountdown(secondsLeft)}</span>
            </p>
          )}
        </div>

        <p className="text-center text-sm text-muted-foreground">
          Wrong number?{" "}
          <Link href="/login" className="text-primary underline-offset-4 hover:underline">
            Change phone
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}

export default function PhoneVerifyPage() {
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
        <PhoneVerifyInner />
      </Suspense>
    </main>
  );
}
