"use client";

import { Clock3, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Modal, ModalContent } from "@/components/ui/modal";
import { useSearchStore } from "@/stores/searchStore";
import { cn } from "@/lib/utils";

const VISIBLE_LIMIT = 5;

type RecentSearchesProps = {
  onSelect: (term: string) => void;
  className?: string;
};

export function RecentSearches({ onSelect, className }: RecentSearchesProps) {
  const recentSearches = useSearchStore((s) => s.recentSearches);
  const removeRecentSearch = useSearchStore((s) => s.removeRecentSearch);
  const clearRecentSearches = useSearchStore((s) => s.clearRecentSearches);
  const [showAllOpen, setShowAllOpen] = useState(false);

  if (!recentSearches.length) return null;

  const visible = recentSearches.slice(0, VISIBLE_LIMIT);
  const hasMore = recentSearches.length > VISIBLE_LIMIT;

  return (
    <section className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-foreground">Recent searches</h2>
        {hasMore || recentSearches.length > 0 ? (
          <button
            type="button"
            onClick={() => setShowAllOpen(true)}
            className="text-sm font-medium text-primary hover:underline"
          >
            Show all
          </button>
        ) : null}
      </div>

      <ul className="overflow-hidden rounded-xl border border-border/70 bg-card">
        {visible.map((term) => (
          <li
            key={term}
            className="flex items-center gap-2 border-b border-border/50 last:border-b-0"
          >
            <button
              type="button"
              onClick={() => onSelect(term)}
              className="flex min-w-0 flex-1 items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted/40"
            >
              <Clock3 className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="truncate">{term}</span>
            </button>
            <button
              type="button"
              onClick={() => removeRecentSearch(term)}
              className="mr-2 rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label={`Remove ${term}`}
            >
              <X className="h-4 w-4" />
            </button>
          </li>
        ))}
      </ul>

      <Modal open={showAllOpen} onOpenChange={setShowAllOpen}>
        <ModalContent
          title="Recent searches"
          description="All of your recent people searches on LinkMe."
          className="max-h-[80vh] overflow-y-auto"
        >
          {recentSearches.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent searches.</p>
          ) : (
            <ul className="space-y-1">
              {recentSearches.map((term) => (
                <li
                  key={term}
                  className="flex items-center gap-2 rounded-lg border border-border/50 px-2"
                >
                  <button
                    type="button"
                    onClick={() => {
                      onSelect(term);
                      setShowAllOpen(false);
                    }}
                    className="flex min-w-0 flex-1 items-center gap-3 px-2 py-2.5 text-left text-sm hover:underline"
                  >
                    <Clock3 className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="truncate">{term}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => removeRecentSearch(term)}
                    className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
                    aria-label={`Remove ${term}`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
          {recentSearches.length > 0 ? (
            <div className="mt-4 flex justify-end">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  clearRecentSearches();
                  setShowAllOpen(false);
                }}
              >
                Clear all
              </Button>
            </div>
          ) : null}
        </ModalContent>
      </Modal>
    </section>
  );
}
