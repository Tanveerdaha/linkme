"use client";

import { ImageIcon, FileText } from "lucide-react";

import type { ProfileStatistics } from "@/types";
import { cn } from "@/lib/utils";

type ProfileStatsProps = {
  statistics?: ProfileStatistics | null;
  className?: string;
};

export function ProfileStats({ statistics, className }: ProfileStatsProps) {
  if (!statistics) return null;
  return (
    <div className={cn("flex flex-wrap gap-4 text-sm", className)}>
      <div className="inline-flex items-center gap-1.5 text-muted-foreground">
        <FileText className="h-4 w-4" />
        <span className="tabular-nums font-medium text-foreground">{statistics.posts}</span>
        <span>{statistics.posts === 1 ? "post" : "posts"}</span>
      </div>
      <div className="inline-flex items-center gap-1.5 text-muted-foreground">
        <ImageIcon className="h-4 w-4" />
        <span className="tabular-nums font-medium text-foreground">{statistics.media}</span>
        <span>{statistics.media === 1 ? "media" : "media"}</span>
      </div>
    </div>
  );
}
