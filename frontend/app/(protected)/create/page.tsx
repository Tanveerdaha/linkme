"use client";

import { CreatePost } from "@/components/posts/CreatePost";
import { BottomNav } from "@/components/layout/bottom-nav";

export default function CreatePostPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8 pb-20 md:pb-10">
      <h1 className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight">
        Create a post
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Share text, images, or video with your network.
      </p>
      <div className="mt-6 rounded-2xl border border-border/70 bg-card/80 p-4 sm:p-6">
        <CreatePost />
      </div>
      <BottomNav active="/create" />
    </main>
  );
}
