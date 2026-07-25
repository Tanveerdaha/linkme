"use client";

import { cn } from "@/lib/utils";
import { passwordStrength } from "@/types/forms";

const labels = ["Too weak", "Weak", "Fair", "Good", "Strong"];

type PasswordStrengthProps = {
  password: string;
};

export function PasswordStrength({ password }: PasswordStrengthProps) {
  if (!password) return null;
  const score = passwordStrength(password);

  return (
    <div className="space-y-1.5" aria-live="polite">
      <div className="flex gap-1">
        {Array.from({ length: 4 }).map((_, index) => (
          <span
            key={index}
            className={cn(
              "h-1.5 flex-1 rounded-full bg-muted transition-colors duration-300",
              index < score && score <= 1 && "bg-destructive",
              index < score && score === 2 && "bg-amber-500",
              index < score && score === 3 && "bg-primary/70",
              index < score && score >= 4 && "bg-primary",
            )}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">{labels[score]}</p>
    </div>
  );
}
