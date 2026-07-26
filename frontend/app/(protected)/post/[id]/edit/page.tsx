"use client";

import { useParams } from "next/navigation";

import { BottomNav } from "@/components/layout/bottom-nav";
import { EditPost } from "@/components/posts/EditPost";

export default function EditPostPage() {
  const params = useParams<{ id: string }>();
  const postId = params?.id;

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8 pb-20 md:pb-10">
      <h1 className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight">
        Edit post
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Update your post, then save or cancel.
      </p>
      <div className="mt-6 rounded-2xl border border-border/70 bg-card/80 p-4 sm:p-6">
        {postId ? <EditPost postId={postId} /> : null}
      </div>
      <BottomNav active="/home" />
    </main>
  );
}
