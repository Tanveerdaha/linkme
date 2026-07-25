"use client";

import { UserSearchCard } from "@/components/search/UserSearchCard";
import type { UserSearchResult } from "@/types";

type UserCardProps = {
  user: UserSearchResult;
  className?: string;
};

/** Thin wrapper kept for older imports — prefer UserSearchCard. */
export function UserCard({ user, className }: UserCardProps) {
  return <UserSearchCard user={user} className={className} />;
}
