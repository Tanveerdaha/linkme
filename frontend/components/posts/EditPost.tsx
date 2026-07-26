"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { PostMedia } from "@/components/feed/PostMedia";
import { Button } from "@/components/ui/button";
import { Loader } from "@/components/ui/loader";
import { getApiErrorMessage } from "@/services/api";
import { getPost, updatePost } from "@/services/posts";
import { useAuthStore } from "@/stores/authStore";
import { useFeedStore } from "@/stores/feedStore";
import type { Post, PostVisibility } from "@/types";

type EditPostProps = {
  postId: string;
};

export function EditPost({ postId }: EditPostProps) {
  const router = useRouter();
  const currentUser = useAuthStore((s) => s.user);
  const updateStorePost = useFeedStore((s) => s.updatePost);

  const [post, setPost] = useState<Post | null>(null);
  const [content, setContent] = useState("");
  const [visibility, setVisibility] = useState<PostVisibility>("PUBLIC");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getPost(postId);
        if (cancelled) return;
        if (currentUser?.username && data.author.username !== currentUser.username) {
          setError("You can only edit your own posts.");
          setPost(null);
          return;
        }
        setPost(data);
        setContent(data.content || "");
        setVisibility(data.visibility);
      } catch (err) {
        if (!cancelled) {
          setError(getApiErrorMessage(err, "Could not load post"));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [postId, currentUser?.username]);

  const remaining = 5000 - content.length;
  const canSave = useMemo(() => {
    if (saving || !post) return false;
    const trimmed = content.trim();
    if (!trimmed && !(post.media?.length > 0)) return false;
    if (content.length > 5000) return false;
    return true;
  }, [content, post, saving]);

  function handleCancel() {
    router.back();
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!post || !canSave) return;
    setSaving(true);
    try {
      const updated = await updatePost(post.id, {
        content: content.trim(),
        visibility,
      });
      updateStorePost(updated);
      toast.success("Post updated");
      router.push(`/post/${updated.id}`);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not update post"));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader className="h-6 w-6" />
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="space-y-4 py-8 text-center">
        <p className="text-sm text-destructive">{error || "Post not found"}</p>
        <Button variant="outline" onClick={handleCancel}>
          Go back
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="mx-auto w-full max-w-2xl space-y-6">
      <div>
        <label htmlFor="edit-post-content" className="sr-only">
          Post content
        </label>
        <textarea
          id="edit-post-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Update your post…"
          rows={8}
          className="w-full resize-y rounded-xl border border-border bg-card/80 px-4 py-3 text-[15px] leading-relaxed outline-none ring-ring focus:ring-2"
          maxLength={5000}
          disabled={saving}
          autoFocus
        />
        <div className="mt-1.5 flex items-center justify-between text-xs text-muted-foreground">
          <span>{remaining} characters left</span>
          <select
            value={visibility}
            onChange={(e) => setVisibility(e.target.value as PostVisibility)}
            disabled={saving}
            className="rounded-md border border-border bg-background px-2 py-1"
            aria-label="Visibility"
          >
            <option value="PUBLIC">Public</option>
            <option value="CONNECTIONS_ONLY">Connections</option>
            <option value="PRIVATE">Private</option>
          </select>
        </div>
      </div>

      {post.media?.length ? (
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">Existing media</p>
          <PostMedia media={post.media} />
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-end gap-3 border-t border-border/60 pt-4">
        <Button type="button" variant="outline" onClick={handleCancel} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" disabled={!canSave} size="lg">
          {saving ? "Saving…" : "Save"}
        </Button>
      </div>
    </form>
  );
}
