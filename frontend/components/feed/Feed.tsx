"use client";

import { useCallback, useEffect } from "react";

import { FeedSkeleton } from "@/components/feed/FeedSkeleton";
import { InfiniteScroll } from "@/components/feed/InfiniteScroll";
import { PostCard } from "@/components/feed/PostCard";
import { getApiErrorMessage } from "@/services/api";
import { cursorFromUrl, getPublicFeed, getUserFeed } from "@/services/feed";
import { getAuthorPosts } from "@/services/posts";
import { useFeedStore } from "@/stores/feedStore";

type FeedProps = {
  mode: "public" | "user" | "author";
  username?: string;
  emptyMessage?: string;
};

export function Feed({
  mode,
  username,
  emptyMessage = "No posts yet. Be the first to share something.",
}: FeedProps) {
  const {
    posts,
    loading,
    loadingMore,
    cursor,
    hasMore,
    error,
    setMode,
    setLoading,
    setLoadingMore,
    setError,
    setPosts,
    appendPosts,
    resetFeed,
  } = useFeedStore();

  const fetchPage = useCallback(
    async (nextCursor: string | null, append: boolean) => {
      if (append) setLoadingMore(true);
      else setLoading(true);
      setError(null);
      try {
        const page =
          mode === "user"
            ? await getUserFeed(nextCursor)
            : mode === "author" && username
              ? await getAuthorPosts(username, nextCursor)
              : await getPublicFeed(nextCursor);

        const next = cursorFromUrl(page.next);
        if (append) {
          appendPosts(page.results, next, Boolean(page.next));
        } else {
          setPosts(page.results, next, Boolean(page.next));
        }
      } catch (err) {
        setError(getApiErrorMessage(err, "Could not load feed"));
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [
      mode,
      username,
      appendPosts,
      setError,
      setLoading,
      setLoadingMore,
      setPosts,
    ],
  );

  useEffect(() => {
    resetFeed();
    setMode(mode);
    void fetchPage(null, false);
    // Intentionally re-fetch when mode/username changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, username]);

  const onLoadMore = useCallback(() => {
    if (!hasMore || loading || loadingMore) return;
    void fetchPage(cursor, true);
  }, [cursor, fetchPage, hasMore, loading, loadingMore]);

  if (loading && posts.length === 0) {
    return <FeedSkeleton count={4} />;
  }

  if (error && posts.length === 0) {
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-6 text-sm text-destructive">
        {error}
      </div>
    );
  }

  if (!loading && posts.length === 0) {
    return (
      <div className="px-2 py-12 text-center text-sm text-muted-foreground">{emptyMessage}</div>
    );
  }

  return (
    <div>
      <div className="divide-y divide-border/60">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
      {loadingMore ? <FeedSkeleton count={1} /> : null}
      <InfiniteScroll hasMore={hasMore} loading={loading || loadingMore} onLoadMore={onLoadMore} />
    </div>
  );
}
