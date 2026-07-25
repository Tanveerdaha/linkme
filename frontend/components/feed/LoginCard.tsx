"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { PasswordInput } from "@/components/auth/PasswordInput";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

export function LoginCard() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(loginValue.trim(), password);
      toast.success("Welcome back");
      router.push("/home");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Login failed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="animate-fade-up rounded-2xl border border-border/70 bg-card/85 p-5 shadow-sm backdrop-blur-sm">
      <p className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold tracking-tight">
        LinkMe
      </p>
      <p className="mt-1 text-sm text-muted-foreground">Sign in to post and follow your feed.</p>
      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        <input
          type="text"
          autoComplete="username"
          placeholder="Email or username"
          value={loginValue}
          onChange={(e) => setLoginValue(e.target.value)}
          required
          className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none ring-ring focus:ring-2"
        />
        <PasswordInput
          autoComplete="current-password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="border-border bg-background shadow-none"
        />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Signing in…" : "Log in"}
        </Button>
      </form>
      <p className="mt-3 text-center text-sm text-muted-foreground">
        New here?{" "}
        <Link href="/signup" className="font-medium text-primary hover:underline">
          Create an account
        </Link>
      </p>
    </section>
  );
}
