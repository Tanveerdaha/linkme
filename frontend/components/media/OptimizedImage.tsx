"use client";

import Image from "next/image";
import { useState } from "react";

import { cn } from "@/lib/utils";

type OptimizedImageProps = {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  fill?: boolean;
  className?: string;
  sizes?: string;
  priority?: boolean;
};

/**
 * Next.js Image wrapper with graceful fallback for non-optimizable URLs.
 */
export function OptimizedImage({
  src,
  alt,
  width,
  height,
  fill,
  className,
  sizes = "(max-width: 768px) 100vw, 640px",
  priority = false,
}: OptimizedImageProps) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src || undefined}
        alt={alt}
        loading="lazy"
        className={cn(className)}
        width={width}
        height={height}
      />
    );
  }

  if (fill) {
    return (
      <Image
        src={src}
        alt={alt}
        fill
        sizes={sizes}
        priority={priority}
        className={cn(className)}
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    <Image
      src={src}
      alt={alt}
      width={width ?? 640}
      height={height ?? 360}
      sizes={sizes}
      priority={priority}
      className={cn(className)}
      onError={() => setFailed(true)}
    />
  );
}
