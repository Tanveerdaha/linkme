"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { toast } from "sonner";

import { PasswordInput } from "@/components/auth/PasswordInput";
import { PasswordStrength } from "@/components/auth/PasswordStrength";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getApiErrorMessage } from "@/services/api";
import { confirmPasswordReset } from "@/services/auth";
import { resetPasswordSchema, type ResetPasswordFormValues } from "@/types/forms";

export default function ResetPasswordPage() {
  const router = useRouter();
  const params = useParams<{ token?: string | string[] }>();
  const rawToken = params?.token;
  const token = Array.isArray(rawToken) ? rawToken.join("/") : rawToken;
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: "", confirm_password: "" },
  });

  const password = watch("password");

  const onSubmit = handleSubmit(async (values) => {
    if (!token) {
      toast.error("Reset token is missing");
      return;
    }
    setSubmitting(true);
    try {
      const decoded = decodeURIComponent(token);
      const result = await confirmPasswordReset(decoded, values.password);
      toast.success(result.message);
      router.push("/login");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to reset password"));
    } finally {
      setSubmitting(false);
    }
  });

  if (!token) {
    return (
      <main className="mx-auto flex min-h-[calc(100vh-3.5rem)] w-full max-w-md items-center px-4 py-10">
        <Card className="w-full">
          <CardHeader>
            <CardTitle className="font-[family-name:var(--font-fraunces)] text-2xl">
              Invalid link
            </CardTitle>
            <CardDescription>This password reset link is missing a token.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full">
              <Link href="/forgot-password">Request a new link</Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3.5rem)] w-full max-w-md items-center px-4 py-10">
      <Card className="w-full animate-fade-up">
        <CardHeader>
          <CardTitle className="font-[family-name:var(--font-fraunces)] text-2xl">
            Reset password
          </CardTitle>
          <CardDescription>Choose a new password for your LinkMe account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <label htmlFor="password" className="text-sm font-medium">
                New password
              </label>
              <PasswordInput id="password" autoComplete="new-password" {...register("password")} />
              <PasswordStrength password={password || ""} />
              {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
            </div>
            <div className="space-y-1.5">
              <label htmlFor="confirm_password" className="text-sm font-medium">
                Confirm password
              </label>
              <PasswordInput
                id="confirm_password"
                autoComplete="new-password"
                {...register("confirm_password")}
              />
              {errors.confirm_password && (
                <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
              )}
            </div>
            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting ? "Saving…" : "Update password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
