"use client";

import { toast as sonnerToast } from "sonner";

/**
 * Thin Toast API over Sonner so call sites stay stable if the library changes.
 */
export const toast = {
  success: (message: string) => sonnerToast.success(message),
  error: (message: string) => sonnerToast.error(message),
  info: (message: string) => sonnerToast.message(message),
  promise: sonnerToast.promise,
};

export { Toaster } from "sonner";
