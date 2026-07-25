"use client";

import { cn } from "@/lib/utils";

type CoverImageProps = {
  src?: string | null;
  className?: string;
};

export function CoverImage({ src, className }: CoverImageProps) {
  return (
    <div
      className={cn(
        "relative h-40 w-full overflow-hidden sm:h-52",
        "bg-[linear-gradient(135deg,color-mix(in_oklab,var(--primary)_35%,transparent),color-mix(in_oklab,var(--accent)_25%,transparent))]",
        className,
      )}
      style={
        src
          ? {
              backgroundImage: `url(${src})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }
          : undefined
      }
      role="img"
      aria-label={src ? "Cover image" : "Default cover"}
    />
  );
}
