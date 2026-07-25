"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { AuthSplitCard } from "@/components/auth/AuthSplitCard";
import { AuthDivider, GoogleLoginButton } from "@/components/auth/GoogleLoginButton";
import { OtpInput, OTP_CODE_LENGTH } from "@/components/auth/OtpInput";
import { PasswordInput } from "@/components/auth/PasswordInput";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getApiErrorMessage } from "@/services/api";
import { sendPhoneOtp } from "@/services/auth";
import { useAuthStore } from "@/stores/authStore";
import {
  loginSchema,
  phoneSchema,
  type LoginFormValues,
  type PhoneFormValues,
} from "@/types/forms";

type AuthMode = "email" | "phone";

function formatCountdown(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const loginWithPhone = useAuthStore((s) => s.loginWithPhone);

  const [mode, setMode] = useState<AuthMode>("email");
  const [submitting, setSubmitting] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpError, setOtpError] = useState<string | null>(null);
  const [otpSentTo, setOtpSentTo] = useState<string | null>(null);
  const [resendSeconds, setResendSeconds] = useState(0);
  const verifyingRef = useRef(false);

  const emailForm = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { login: "", password: "" },
  });

  const phoneForm = useForm<PhoneFormValues>({
    resolver: zodResolver(phoneSchema),
    defaultValues: { phone_number: "" },
  });

  useEffect(() => {
    if (resendSeconds <= 0) return;
    const id = window.setInterval(() => {
      setResendSeconds((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => window.clearInterval(id);
  }, [resendSeconds]);

  const switchToPhone = () => {
    setMode("phone");
    setOtp("");
    setOtpError(null);
    setOtpSentTo(null);
    setResendSeconds(0);
  };

  const switchToEmail = () => {
    setMode("email");
    setOtp("");
    setOtpError(null);
    setOtpSentTo(null);
    setResendSeconds(0);
  };

  const handleSendOtp = phoneForm.handleSubmit(async (values) => {
    if (resendSeconds > 0 && otpSentTo) {
      toast.error(`Please wait ${resendSeconds}s before requesting a new code`);
      return;
    }
    setSendingOtp(true);
    setOtpError(null);
    try {
      const result = await sendPhoneOtp(values.phone_number);
      setOtpSentTo(result.phone_number);
      setOtp("");
      setResendSeconds(result.resend_available_in ?? 120);
      toast.success(result.message || "Verification code sent on WhatsApp");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to send verification code"));
    } finally {
      setSendingOtp(false);
    }
  });

  const onEmailSubmit = emailForm.handleSubmit(async (values) => {
    setSubmitting(true);
    try {
      await login(values.login, values.password);
      toast.success("Welcome back");
      router.push("/home");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to log in"));
    } finally {
      setSubmitting(false);
    }
  });

  const verifyPhoneCode = useCallback(
    async (code: string) => {
      if (!otpSentTo || code.length !== OTP_CODE_LENGTH || verifyingRef.current) return;
      verifyingRef.current = true;
      setSubmitting(true);
      setOtpError(null);
      try {
        await loginWithPhone(otpSentTo, code);
        toast.success("Welcome back");
        router.push("/home");
      } catch (error) {
        setOtpError(getApiErrorMessage(error, "Invalid verification code"));
        toast.error(getApiErrorMessage(error, "Invalid verification code"));
        setOtp("");
      } finally {
        setSubmitting(false);
        verifyingRef.current = false;
      }
    },
    [loginWithPhone, otpSentTo, router],
  );

  const onPhoneVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    const valid = await phoneForm.trigger("phone_number");
    if (!valid) return;
    if (!otpSentTo) {
      toast.error("Request a verification code first");
      return;
    }
    if (otp.length !== OTP_CODE_LENGTH) {
      setOtpError("Enter the 6-digit code");
      return;
    }
    await verifyPhoneCode(otp);
  };

  return (
    <AuthSplitCard
      panelTitle="Welcome back to LinkMe"
      panelSubtitle="Pick up where you left off. Your network, messages, and feed are waiting."
    >
      <div className="flex min-h-full flex-col space-y-4 sm:space-y-5">
        <div>
          <h2 className="font-[family-name:var(--font-fraunces)] text-xl font-semibold tracking-tight sm:text-2xl">
            Log in
          </h2>
          <p
            key={`subtitle-${mode}`}
            className="animate-auth-fade-swap mt-1 text-sm text-muted-foreground"
          >
            {mode === "phone"
              ? "Sign in with your WhatsApp phone number."
              : "Sign in with Google or your email."}
          </p>
        </div>

        <GoogleLoginButton />
        <AuthDivider />

        <div
          key={mode}
          className={
            mode === "phone" ? "animate-auth-panel-phone" : "animate-auth-panel-email"
          }
        >
          {mode === "email" ? (
            <form onSubmit={onEmailSubmit} className="space-y-3.5 sm:space-y-4" noValidate>
              <div className="space-y-1.5">
                <label htmlFor="login" className="text-sm font-medium">
                  Email or username
                </label>
                <Input id="login" autoComplete="username" {...emailForm.register("login")} />
                {emailForm.formState.errors.login && (
                  <p className="text-xs text-destructive">
                    {emailForm.formState.errors.login.message}
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <label htmlFor="password" className="text-sm font-medium">
                    Password
                  </label>
                  <Link href="/forgot-password" className="text-xs text-primary hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <PasswordInput
                  id="password"
                  autoComplete="current-password"
                  {...emailForm.register("password")}
                />
                {emailForm.formState.errors.password && (
                  <p className="text-xs text-destructive">
                    {emailForm.formState.errors.password.message}
                  </p>
                )}
              </div>
              <Button className="h-11 w-full sm:h-10" type="submit" disabled={submitting}>
                {submitting ? "Signing in…" : "Login"}
              </Button>
            </form>
          ) : (
            <form onSubmit={(e) => void onPhoneVerify(e)} className="space-y-3.5 sm:space-y-4" noValidate>
              <div className="space-y-1.5">
                <label htmlFor="phone_number" className="text-sm font-medium">
                  Phone number
                </label>
                <Input
                  id="phone_number"
                  type="tel"
                  inputMode="tel"
                  autoComplete="tel"
                  placeholder="+923001234567"
                  disabled={sendingOtp || submitting}
                  {...phoneForm.register("phone_number")}
                />
                {phoneForm.formState.errors.phone_number ? (
                  <p className="text-xs text-destructive">
                    {phoneForm.formState.errors.phone_number.message}
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    International format with country code (WhatsApp).
                  </p>
                )}
              </div>

              <Button
                type="button"
                variant="outline"
                className="h-11 w-full sm:h-10"
                disabled={sendingOtp || submitting || resendSeconds > 0}
                onClick={() => void handleSendOtp()}
              >
                {sendingOtp
                  ? "Sending code…"
                  : otpSentTo
                    ? resendSeconds > 0
                      ? `Resend OTP in ${formatCountdown(resendSeconds)}`
                      : "Resend OTP"
                    : "Get OTP"}
              </Button>

              <div className="space-y-1.5">
                <OtpInput
                  value={otp}
                  onChange={(next) => {
                    setOtp(next);
                    setOtpError(null);
                    if (next.length === OTP_CODE_LENGTH) {
                      void verifyPhoneCode(next);
                    }
                  }}
                  disabled={submitting || !otpSentTo}
                  error={Boolean(otpError)}
                  autoFocus={Boolean(otpSentTo)}
                />
                {otpError ? (
                  <p className="text-xs text-destructive">{otpError}</p>
                ) : otpSentTo ? (
                  <p className="text-xs text-muted-foreground">
                    Enter the 6-digit WhatsApp code. Paste works too.
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Request an OTP first, then enter the code here.
                  </p>
                )}
              </div>

              <Button
                className="h-11 w-full sm:h-10"
                type="submit"
                disabled={submitting || !otpSentTo || otp.length !== OTP_CODE_LENGTH}
              >
                {submitting ? "Verifying…" : "Login"}
              </Button>
            </form>
          )}
        </div>

        <div className="mt-auto flex items-center justify-between gap-3 border-t border-border/50 pt-4 text-sm sm:mt-0 sm:border-0 sm:pt-1">
          <Link href="/signup" className="text-primary underline-offset-4 hover:underline">
            Create account
          </Link>
          <button
            type="button"
            key={`switch-${mode}`}
            onClick={mode === "email" ? switchToPhone : switchToEmail}
            className="animate-auth-fade-swap font-medium text-primary underline-offset-4 transition-colors hover:underline"
          >
            {mode === "email" ? "Continue with phone" : "Continue with email"}
          </button>
        </div>
      </div>
    </AuthSplitCard>
  );
}
