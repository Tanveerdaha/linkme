"use client";

import Link from "next/link";
import { Globe, Lock, Users } from "lucide-react";

import { SafetyMenu } from "@/components/moderation/SafetyMenu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { Post, PostVisibility } from "@/types";

function initials(name: string, username: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (username.slice(0, 2) || "LM").toUpperCase();
}

export function formatRelativeTime(iso: string | null) {
  if (!iso) return "";
  const date = new Date(iso);
  const diff = Date.now() - date.getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function visibilityLabel(visibility: PostVisibility) {
  switch (visibility) {
    case "PRIVATE":
      return { label: "Private", Icon: Lock };
    case "CONNECTIONS_ONLY":
      return { label: "Connections", Icon: Users };
    default:
      return { label: "Public", Icon: Globe };
  }
}

type PostHeaderProps = {
  post: Post;
};

export function PostHeader({ post }: PostHeaderProps) {
  const { author, visibility, published_at, created_at } = post;
  const time = formatRelativeTime(published_at || created_at);
  const headline = (author.headline || "").trim();
  const { label, Icon } = visibilityLabel(visibility);
  const timestamp = published_at || created_at;

  return (
    <div className="flex gap-3">
      <Link href={`/u/${author.username}`} className="shrink-0 self-start">
        <Avatar className="h-12 w-12">
          {author.avatar ? <AvatarImage src={author.avatar} alt={author.name} /> : null}
          <AvatarFallback>{initials(author.name, author.username)}</AvatarFallback>
        </Avatar>
      </Link>

      <div className="min-w-0 flex-1">
        <div className="flex items-start gap-2">
          <div className="min-w-0 flex-1 leading-snug">
            <Link
              href={`/u/${author.username}`}
              className="block truncate text-[15px] font-semibold text-foreground hover:underline"
            >
              {author.name}
            </Link>
            {headline ? (
              <p className="mt-0.5 truncate text-[13px] text-muted-foreground">{headline}</p>
            ) : null}
            <p className="mt-0.5 flex flex-wrap items-center gap-x-1 text-xs text-muted-foreground">
              {time ? (
                <time dateTime={timestamp || undefined}>{time}</time>
              ) : null}
              {time ? <span aria-hidden>·</span> : null}
              <span className="inline-flex items-center gap-0.5">
                <Icon className="h-3 w-3" aria-hidden />
                <span>{label}</span>
              </span>
            </p>
          </div>
          <SafetyMenu
            contentType="POST"
            objectId={String(post.id)}
            username={author.username}
            label={`this post by ${author.name}`}
            showBlock
          />
        </div>
      </div>
    </div>
  );
}
