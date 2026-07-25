"use client";

import { OptimizedImage } from "@/components/media/OptimizedImage";
import { cn } from "@/lib/utils";
import type { PostMedia as PostMediaType } from "@/types";

type PostMediaProps = {
  media: PostMediaType[];
};

export function PostMedia({ media }: PostMediaProps) {
  if (!media.length) return null;

  return (
    <div
      className={cn(
        "mt-2.5 grid gap-2 overflow-hidden rounded-xl border border-border/50 bg-muted/30",
        media.length > 1 ? "grid-cols-2" : "grid-cols-1",
      )}
    >
      {media.map((item) => (
        <div key={item.id} className="relative bg-muted/40">
          {item.media_type === "IMAGE" && item.url ? (
            <OptimizedImage
              src={item.url}
              alt=""
              width={item.width || 640}
              height={item.height || 360}
              className="max-h-[28rem] w-full object-cover"
              sizes="(max-width: 768px) 100vw, 640px"
            />
          ) : null}
          {item.media_type === "VIDEO" ? (
            item.processing_status === "READY" && item.url ? (
              <video
                src={item.url}
                poster={item.thumbnail_url || undefined}
                controls
                playsInline
                className="max-h-[28rem] w-full bg-black"
              />
            ) : (
              <div className="flex aspect-video items-center justify-center bg-muted/50 text-sm text-muted-foreground">
                {item.processing_status === "FAILED"
                  ? "Video processing failed"
                  : "Processing video…"}
              </div>
            )
          ) : null}
        </div>
      ))}
    </div>
  );
}
