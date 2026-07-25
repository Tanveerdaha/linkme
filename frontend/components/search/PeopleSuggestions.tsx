"use client";

import { useEffect } from "react";

import { UserSearchCard } from "@/components/search/UserSearchCard";
import { Loader } from "@/components/ui/loader";
import { useSearchStore } from "@/stores/searchStore";
import { cn } from "@/lib/utils";

type PeopleSuggestionsProps = {
  limit?: number;
  className?: string;
};

export function PeopleSuggestions({
  limit = 4,
  className,
}: PeopleSuggestionsProps) {
  const suggestions = useSearchStore((s) => s.suggestions);
  const loading = useSearchStore((s) => s.suggestionsLoading);
  const loadSuggestions = useSearchStore((s) => s.loadSuggestions);

  useEffect(() => {
    if (!suggestions.length && !loading) {
      void loadSuggestions();
    }
  }, [suggestions.length, loading, loadSuggestions]);

  if (loading && !suggestions.length) {
    return (
      <section className={cn("space-y-3", className)}>
        <h2 className="text-sm font-semibold text-foreground">
          People you may know
        </h2>
        <div className="flex justify-center py-8">
          <Loader label="Loading suggestions" />
        </div>
      </section>
    );
  }

  if (!suggestions.length) return null;

  const visible = suggestions.slice(0, limit);

  return (
    <section className={cn("space-y-3", className)}>
      <h2 className="text-sm font-semibold text-foreground">
        People you may know
      </h2>
      <ul className="grid gap-2 sm:grid-cols-2">
        {visible.map((user) => (
          <li key={user.username}>
            <UserSearchCard user={user} />
          </li>
        ))}
      </ul>
    </section>
  );
}
