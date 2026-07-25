"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { toast } from "sonner";

import { AuthSplitCard } from "@/components/auth/AuthSplitCard";
import { AuthDivider, GoogleLoginButton } from "@/components/auth/GoogleLoginButton";
import { PasswordInput } from "@/components/auth/PasswordInput";
import { PasswordStrength } from "@/components/auth/PasswordStrength";
import {
  UsernameInput,
  type UsernameAvailabilityState,
} from "@/components/auth/UsernameInput";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getApiErrorMessage } from "@/services/api";
import { signup } from "@/services/auth";
import { signupSchema, type SignupFormValues } from "@/types/forms";

export default function SignupPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [usernameAvailability, setUsernameAvailability] =
    useState<UsernameAvailabilityState>("idle");
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      username: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const password = watch("password");

  const onSubmit = handleSubmit(async (values) => {
    if (usernameAvailability === "taken" || usernameAvailability === "invalid") {
      toast.error("Please choose an available username");
      return;
    }
    setSubmitting(true);
    try {
      const result = await signup({
        email: values.email.toLowerCase(),
        username: values.username.toLowerCase(),
        password: values.password,
        first_name: values.first_name,
        last_name: values.last_name,
      });
      toast.success(result.message);
      router.push(`/verify-email?email=${encodeURIComponent(result.email)}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Unable to create account"));
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <AuthSplitCard
      panelTitle="Join LinkMe today"
      panelSubtitle="Create your profile and start building meaningful professional connections."
    >
      <div className="flex min-h-full flex-col space-y-4 sm:space-y-5">
        <div>
          <h2 className="font-[family-name:var(--font-fraunces)] text-xl font-semibold tracking-tight sm:text-2xl">
            Create account
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Continue with Google or sign up with email.
          </p>
        </div>

        <GoogleLoginButton />
        <AuthDivider />

        <form onSubmit={onSubmit} className="space-y-3.5 sm:space-y-4" noValidate>
          <div className="grid gap-3.5 sm:grid-cols-2 sm:gap-4">
            <div className="space-y-1.5">
              <label htmlFor="first_name" className="text-sm font-medium">
                First name
              </label>
              <Input id="first_name" autoComplete="given-name" {...register("first_name")} />
              {errors.first_name && (
                <p className="text-xs text-destructive">{errors.first_name.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <label htmlFor="last_name" className="text-sm font-medium">
                Last name
              </label>
              <Input id="last_name" autoComplete="family-name" {...register("last_name")} />
              {errors.last_name && (
                <p className="text-xs text-destructive">{errors.last_name.message}</p>
              )}
            </div>
          </div>
          <div className="space-y-1.5">
            <label htmlFor="username" className="text-sm font-medium">
              Username
            </label>
            <Controller
              name="username"
              control={control}
              render={({ field }) => (
                <UsernameInput
                  value={field.value}
                  onChange={field.onChange}
                  error={errors.username?.message}
                  onAvailabilityChange={setUsernameAvailability}
                />
              )}
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <Input id="email" type="email" autoComplete="email" {...register("email")} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>
          <div className="space-y-1.5">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <PasswordInput
              id="password"
              autoComplete="new-password"
              {...register("password")}
            />
            <PasswordStrength password={password || ""} />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
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
          <Button
            className="h-11 w-full sm:h-10"
            type="submit"
            disabled={
              submitting ||
              usernameAvailability === "checking" ||
              usernameAvailability === "taken" ||
              usernameAvailability === "invalid"
            }
          >
            {submitting ? "Creating account…" : "Create Account"}
          </Button>
        </form>

        <div className="mt-auto flex items-center justify-between gap-3 border-t border-border/50 pt-4 text-sm sm:mt-0 sm:border-0 sm:pt-1">
          <Link href="/login" className="text-primary underline-offset-4 hover:underline">
            Log in
          </Link>
          <Link
            href="/login"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Continue with phone
          </Link>
        </div>
      </div>
    </AuthSplitCard>
  );
}
