"use client";

import { useEffect, useState } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { checkUsernameAvailability } from "@/services/users";

export type UsernameAvailabilityState = "idle" | "checking" | "available" | "taken" | "invalid";

export type UsernameInputProps = {
  value: string;
  onChange: (value: string) => void;
  error?: string;
  availability?: UsernameAvailabilityState;
  onAvailabilityChange?: (state: UsernameAvailabilityState) => void;
  /** Skip availability API when value matches the current handle (profile edit). */
  currentUsername?: string;
  id?: string;
  name?: string;
  disabled?: boolean;
  autoComplete?: string;
  className?: string;
};

const DEBOUNCE_MS = 500;

export function UsernameInput({
  value,
  onChange,
  error,
  availability: controlledAvailability,
  onAvailabilityChange,
  currentUsername,
  id = "username",
  name = "username",
  disabled,
  autoComplete = "username",
  className,
}: UsernameInputProps) {
  const [internalAvailability, setInternalAvailability] =
    useState<UsernameAvailabilityState>("idle");

  const availability = controlledAvailability ?? internalAvailability;

  function setAvailability(next: UsernameAvailabilityState) {
    setInternalAvailability(next);
    onAvailabilityChange?.(next);
  }

  useEffect(() => {
    const trimmed = value.trim().toLowerCase();
    if (!trimmed || trimmed.length < 3) {
      setAvailability("idle");
      return;
    }
    if (currentUsername && trimmed === currentUsername.toLowerCase()) {
      setAvailability("available");
      return;
    }

    setAvailability("checking");
    const timer = window.setTimeout(() => {
      void checkUsernameAvailability(trimmed)
        .then((result) => {
          if (result.available) {
            setAvailability("available");
          } else if (result.reason?.toLowerCase().includes("already exists")) {
            setAvailability("taken");
          } else {
            setAvailability("invalid");
          }
        })
        .catch(() => setAvailability("idle"));
    }, DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setAvailability is stable enough for debounce
  }, [value, currentUsername]);

  return (
    <div className="space-y-1.5">
      <Input
        id={id}
        name={name}
        value={value}
        disabled={disabled}
        autoComplete={autoComplete}
        className={cn(className)}
        onChange={(event) => onChange(event.target.value.toLowerCase())}
        aria-invalid={Boolean(error) || availability === "taken" || availability === "invalid"}
      />
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
      {!error && availability === "checking" ? (
        <p className="text-xs text-muted-foreground">Checking username…</p>
      ) : null}
      {!error && availability === "available" ? (
        <p className="text-xs text-primary">✓ Username available</p>
      ) : null}
      {!error && availability === "taken" ? (
        <p className="text-xs text-destructive">✕ Username already taken</p>
      ) : null}
      {!error && availability === "invalid" ? (
        <p className="text-xs text-destructive">✕ Username is not valid</p>
      ) : null}
    </div>
  );
}
