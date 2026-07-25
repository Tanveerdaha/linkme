"use client";

import { useQuery } from "@tanstack/react-query";
import { Heart, MessageCircle, PenSquare } from "lucide-react";

import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getProfileActivity } from "@/services/profile";
import type { ActivityItem } from "@/types";

type ActivityTimelineProps = {
  username: string;
};

function formatRelative(iso: string) {
  const date = new Date(iso);
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function iconFor(type: ActivityItem["type"]) {
  if (type === "COMMENT_CREATED") return MessageCircle;
  if (type === "REACTION_CREATED") return Heart;
  return PenSquare;
}

function labelFor(type: ActivityItem["type"], username: string) {
  if (type === "COMMENT_CREATED") return `${username} commented`;
  if (type === "REACTION_CREATED") return `${username} reacted`;
  return `${username} created a post`;
}

export function ActivityTimeline({ username }: ActivityTimelineProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["profile-activity", username],
    queryFn: () => getProfileActivity(username),
    enabled: Boolean(username),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader label="Loading activity" />
      </div>
    );
  }

  if (error) {
    return (
      <p className="py-8 text-center text-sm text-destructive">
        {getApiErrorMessage(error, "Could not load activity")}
      </p>
    );
  }

  if (!data?.length) {
    return (
      <p className="rounded-2xl border border-border/70 bg-card px-5 py-10 text-center text-sm text-muted-foreground">
        No recent activity.
      </p>
    );
  }

  return (
    <ol className="animate-fade-up space-y-0 rounded-2xl border border-border/70 bg-card px-4 py-2 sm:px-5">
      {data.map((item, index) => {
        const Icon = iconFor(item.type);
        return (
          <li
            key={`${item.type}-${item.ref_id || index}`}
            className="flex gap-3 border-b border-border/40 py-4 last:border-0"
          >
            <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
              <Icon className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">
                {labelFor(item.type, username)}
              </p>
              {item.content ? (
                <p className="mt-0.5 line-clamp-2 text-sm text-muted-foreground">
                  {item.content}
                </p>
              ) : null}
              <time className="mt-1 block text-xs text-muted-foreground">
                {formatRelative(item.created_at)}
              </time>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
