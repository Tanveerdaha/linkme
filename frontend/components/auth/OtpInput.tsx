"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type ClipboardEvent,
  type KeyboardEvent,
} from "react";

import { cn } from "@/lib/utils";

const OTP_LENGTH = 6;

type OtpInputProps = {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: boolean;
  autoFocus?: boolean;
  className?: string;
};

function sanitizeDigits(raw: string, max = OTP_LENGTH) {
  return raw.replace(/\D/g, "").slice(0, max);
}

export function OtpInput({
  value,
  onChange,
  disabled,
  error,
  autoFocus,
  className,
}: OtpInputProps) {
  const id = useId();
  const inputsRef = useRef<Array<HTMLInputElement | null>>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const digits = Array.from({ length: OTP_LENGTH }, (_, i) => value[i] || "");

  const focusIndex = useCallback((index: number) => {
    const next = Math.max(0, Math.min(OTP_LENGTH - 1, index));
    const el = inputsRef.current[next];
    el?.focus();
    el?.select();
    setActiveIndex(next);
  }, []);

  useEffect(() => {
    if (autoFocus && !disabled) focusIndex(0);
  }, [autoFocus, disabled, focusIndex]);

  const updateAt = (index: number, nextDigit: string) => {
    const next = digits.map((d, i) => (i === index ? nextDigit : d));
    onChange(next.join(""));
  };

  const handleChange = (index: number, raw: string) => {
    const cleaned = sanitizeDigits(raw);
    if (!cleaned) {
      updateAt(index, "");
      return;
    }
    if (cleaned.length > 1) {
      const merged = sanitizeDigits(`${value.slice(0, index)}${cleaned}${value.slice(index + 1)}`);
      onChange(merged);
      focusIndex(Math.min(merged.length, OTP_LENGTH - 1));
      return;
    }
    updateAt(index, cleaned);
    if (index < OTP_LENGTH - 1) focusIndex(index + 1);
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      e.preventDefault();
      if (digits[index]) {
        updateAt(index, "");
      } else if (index > 0) {
        updateAt(index - 1, "");
        focusIndex(index - 1);
      }
      return;
    }
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      focusIndex(index - 1);
      return;
    }
    if (e.key === "ArrowRight") {
      e.preventDefault();
      focusIndex(index + 1);
      return;
    }
    if (e.key === "Home") {
      e.preventDefault();
      focusIndex(0);
      return;
    }
    if (e.key === "End") {
      e.preventDefault();
      focusIndex(OTP_LENGTH - 1);
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = sanitizeDigits(e.clipboardData.getData("text"));
    if (!pasted) return;
    onChange(pasted);
    focusIndex(Math.min(pasted.length, OTP_LENGTH - 1));
  };

  return (
    <div
      className={cn(
        "flex w-full items-center justify-between gap-1 rounded-xl border border-border/60 bg-muted/20 p-2 sm:gap-2 sm:rounded-2xl sm:p-3",
        error && "border-destructive/40 bg-destructive/[0.03]",
        className,
      )}
      role="group"
      aria-label="One-time passcode"
    >
      {digits.map((digit, index) => {
        const isActive = activeIndex === index && !disabled;
        const showCaret = isActive && !digit;

        return (
          <div key={`${id}-${index}`} className="contents">
            {index === 3 ? (
              <span
                aria-hidden
                className="mx-0.5 h-px w-2 shrink-0 bg-border sm:mx-1 sm:w-4"
              />
            ) : null}
            <div className="relative min-w-0 flex-1">
              <input
                ref={(el) => {
                  inputsRef.current[index] = el;
                }}
                id={index === 0 ? `${id}-otp` : undefined}
                type="text"
                inputMode="numeric"
                autoComplete={index === 0 ? "one-time-code" : "off"}
                pattern="\d*"
                maxLength={1}
                value={digit}
                disabled={disabled}
                placeholder=" "
                aria-label={`Digit ${index + 1} of ${OTP_LENGTH}`}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={handlePaste}
                onFocus={(e) => {
                  setActiveIndex(index);
                  e.target.select();
                }}
                className={cn(
                  "peer h-11 w-full rounded-md border bg-card text-center text-base font-semibold tabular-nums text-foreground outline-none transition-all duration-150 sm:h-14 sm:text-xl",
                  "placeholder:text-transparent",
                  "disabled:cursor-not-allowed disabled:bg-muted/40 disabled:opacity-60",
                  error
                    ? "border-destructive/45 focus:border-destructive focus:ring-2 focus:ring-destructive/20"
                    : digit
                      ? "border-primary/40 text-foreground shadow-[inset_0_-2px_0_0_var(--primary)]"
                      : "border-transparent hover:border-primary/25",
                  !error && isActive && "border-primary ring-2 ring-primary/20",
                )}
              />
              {!digit && !disabled ? (
                <span
                  aria-hidden
                  className={cn(
                    "pointer-events-none absolute left-1/2 top-1/2 h-[2px] w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-muted-foreground/25 sm:w-3.5",
                    showCaret && "animate-pulse bg-primary",
                  )}
                />
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export const OTP_CODE_LENGTH = OTP_LENGTH;
