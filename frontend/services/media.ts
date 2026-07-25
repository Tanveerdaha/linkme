import type { MediaType } from "@/types";

/**
 * Media is uploaded as part of multipart post creation in Phase 2.
 * Helpers below support client-side validation and UX.
 */

export function uploadMediaHint(file: File): "image" | "video" | "unknown" {
  if (file.type.startsWith("image/")) return "image";
  if (file.type.startsWith("video/")) return "video";
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (ext && ["jpg", "jpeg", "png", "webp"].includes(ext)) return "image";
  if (ext && ["mp4", "webm", "mov"].includes(ext)) return "video";
  return "unknown";
}

export function mediaTypeFromHint(hint: "image" | "video" | "unknown"): MediaType | null {
  if (hint === "image") return "IMAGE";
  if (hint === "video") return "VIDEO";
  return null;
}

export const MEDIA_LIMITS = {
  imageMaxBytes: 10 * 1024 * 1024,
  videoMaxBytes: 200 * 1024 * 1024,
  imageAccept: "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp",
  videoAccept: "video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov",
  maxFiles: 10,
} as const;
