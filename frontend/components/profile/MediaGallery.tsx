"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Play } from "lucide-react";

import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getProfileMedia } from "@/services/profile";
import type { ProfileMediaItem } from "@/types";

type MediaGalleryProps = {
  username: string;
};

function MediaTile({ item }: { item: ProfileMediaItem }) {
  const isVideo = item.media_type === "VIDEO";
  const src = isVideo ? item.thumbnail_url || item.url : item.url;
  return (
    <Link
      href={`/post/${item.post_id}`}
      className="group relative aspect-square overflow-hidden rounded-lg bg-muted/40"
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt=""
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          loading="lazy"
        />
      ) : (
        <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
          {isVideo ? "Video" : "Image"}
        </div>
      )}
      {isVideo ? (
        <span className="absolute inset-0 flex items-center justify-center bg-black/20">
          <Play className="h-8 w-8 fill-white text-white drop-shadow" />
        </span>
      ) : null}
    </Link>
  );
}

export function MediaGallery({ username }: MediaGalleryProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["profile-media", username],
    queryFn: () => getProfileMedia(username),
    enabled: Boolean(username),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader label="Loading media" />
      </div>
    );
  }

  if (error) {
    return (
      <p className="py-8 text-center text-sm text-destructive">
        {getApiErrorMessage(error, "Could not load media")}
      </p>
    );
  }

  const items = [...(data?.images || []), ...(data?.videos || [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  if (items.length === 0) {
    return (
      <p className="rounded-2xl border border-border/70 bg-card px-5 py-10 text-center text-sm text-muted-foreground">
        No media yet.
      </p>
    );
  }

  return (
    <div className="animate-fade-up grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3">
      {items.map((item) => (
        <MediaTile key={item.id} item={item} />
      ))}
    </div>
  );
}
