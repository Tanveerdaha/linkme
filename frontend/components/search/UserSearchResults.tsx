"use client";

import { UserCard } from "@/components/search/UserCard";
import { Button } from "@/components/ui/button";
import { Loader } from "@/components/ui/loader";
import type { UserSearchResult } from "@/types";

type UserSearchResultsProps = {
  results: UserSearchResult[];
  loading?: boolean;
  count?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  emptyMessage?: string;
};

export function UserSearchResults({
  results,
  loading,
  count = 0,
  page = 1,
  pageSize = 20,
  onPageChange,
  emptyMessage = "No people found. Try another name or headline.",
}: UserSearchResultsProps) {
  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader label="Searching" />
      </div>
    );
  }

  if (!results.length) {
    return (
      <p className="rounded-2xl border border-dashed border-border/70 px-5 py-12 text-center text-sm text-muted-foreground">
        {emptyMessage}
      </p>
    );
  }

  const totalPages = Math.max(1, Math.ceil(count / pageSize));

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        {count} {count === 1 ? "person" : "people"}
      </p>
      <ul className="space-y-2">
        {results.map((user) => (
          <li key={user.username}>
            <UserCard user={user} />
          </li>
        ))}
      </ul>
      {totalPages > 1 && onPageChange ? (
        <div className="flex items-center justify-center gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </Button>
        </div>
      ) : null}
    </div>
  );
}
