"use client";

import { Toaster } from "sonner";

/** Global toast host (Sonner) used by the Toast helper. */
export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      richColors
      closeButton
      toastOptions={{
        className: "border border-border bg-card text-card-foreground",
      }}
    />
  );
}
