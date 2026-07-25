"use client";

import Link from "next/link";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

type ProfileAvatarProps = {
  name: string;
  username: string;
  src?: string | null;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  href?: string;
};

const sizes = {
  sm: "h-10 w-10",
  md: "h-14 w-14",
  lg: "h-24 w-24 sm:h-28 sm:w-28",
  xl: "h-28 w-28 sm:h-32 sm:w-32",
};

function initials(name: string, username: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return (username.slice(0, 2) || "LM").toUpperCase();
}

export function ProfileAvatar({
  name,
  username,
  src,
  size = "lg",
  className,
  href,
}: ProfileAvatarProps) {
  const avatar = (
    <Avatar className={cn(sizes[size], "border-4 border-card shadow-sm", className)}>
      {src ? <AvatarImage src={src} alt={name} /> : null}
      <AvatarFallback className={size === "sm" || size === "md" ? "text-sm" : "text-lg"}>
        {initials(name, username)}
      </AvatarFallback>
    </Avatar>
  );
  if (href) {
    return (
      <Link href={href} className="shrink-0">
        {avatar}
      </Link>
    );
  }
  return avatar;
}
