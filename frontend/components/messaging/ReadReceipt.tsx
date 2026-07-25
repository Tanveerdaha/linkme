"use client";

import { Check, CheckCheck } from "lucide-react";

import { cn } from "@/lib/utils";

type ReadReceiptProps = {
  status?: "SENT" | "DELIVERED" | "READ" | null;
  className?: string;
};

export function ReadReceipt({ status, className }: ReadReceiptProps) {
  if (!status) return null;
  const read = status === "READ";
  const delivered = status === "DELIVERED" || read;
  return (
    <span
      className={cn(
        "inline-flex items-center",
        read ? "text-primary" : "text-muted-foreground/70",
        className,
      )}
      aria-label={status.toLowerCase()}
    >
      {delivered ? (
        <CheckCheck className="h-3.5 w-3.5" />
      ) : (
        <Check className="h-3.5 w-3.5" />
      )}
    </span>
  );
}
