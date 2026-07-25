"use client";

export function PostSkeleton() {
  return (
    <article className="animate-pulse border-b border-border/60 py-5">
      <div className="flex gap-3">
        <div className="h-11 w-11 shrink-0 rounded-full bg-muted" />
        <div className="min-w-0 flex-1 space-y-3">
          <div className="flex gap-2">
            <div className="h-3.5 w-28 rounded bg-muted" />
            <div className="h-3.5 w-20 rounded bg-muted/70" />
          </div>
          <div className="h-3 w-full rounded bg-muted/80" />
          <div className="h-3 w-[80%] rounded bg-muted/70" />
          <div className="mt-2 h-48 w-full rounded-lg bg-muted/60" />
        </div>
      </div>
    </article>
  );
}

export function FeedSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="divide-y divide-border/60" aria-busy="true" aria-label="Loading feed">
      {Array.from({ length: count }).map((_, i) => (
        <PostSkeleton key={i} />
      ))}
    </div>
  );
}
