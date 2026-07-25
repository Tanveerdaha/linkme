"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { PostCard } from "@/components/feed/PostCard";
import { FeedSkeleton } from "@/components/feed/FeedSkeleton";
import { BottomNav } from "@/components/layout/bottom-nav";
import { SiteHeader } from "@/components/layout/site-header";
import { getApiErrorMessage } from "@/services/api";
import { getPost } from "@/services/posts";
import { useFeedStore } from "@/stores/feedStore";

export default function PostDetailPage() {
  const params = useParams<{ id: string }>();
  const postId = params?.id;
  const setPosts = useFeedStore((s) => s.setPosts);
  const storePost = useFeedStore((s) =>
    postId ? s.posts.find((p) => p.id === postId) : undefined,
  );

  const { data, isLoading, error } = useQuery({
    queryKey: ["post", postId],
    queryFn: () => getPost(postId!),
    enabled: Boolean(postId),
  });

  useEffect(() => {
    if (data) {
      setPosts([data], null, false);
    }
  }, [data, setPosts]);

  const display = storePost || data;

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl px-4 py-6 pb-20 md:pb-8">
        <Link
          href="/"
          className="text-sm text-muted-foreground hover:text-foreground hover:underline"
        >
          ← Back
        </Link>
        <div className="mt-4 rounded-2xl border border-border/70 bg-card/70 px-2 sm:px-3">
          {isLoading ? <FeedSkeleton count={1} /> : null}
          {error ? (
            <p className="px-3 py-8 text-center text-sm text-destructive">
              {getApiErrorMessage(error, "Post not found")}
            </p>
          ) : null}
          {!isLoading && !error && display ? <PostCard post={display} /> : null}
        </div>
      </main>
      <BottomNav active="/" />
    </>
  );
}
