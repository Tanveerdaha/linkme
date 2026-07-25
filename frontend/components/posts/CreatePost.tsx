"use client";

import { useRouter } from "next/navigation";
import { ImagePlus, Trash2, Video } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { UploadProgress } from "@/components/posts/UploadProgress";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import { MEDIA_LIMITS, uploadMediaHint } from "@/services/media";
import { createPost } from "@/services/posts";
import { useFeedStore } from "@/stores/feedStore";
import type { PostVisibility } from "@/types";

type PreviewItem = {
  id: string;
  file: File;
  kind: "image" | "video" | "unknown";
  url: string;
};

export function CreatePost() {
  const router = useRouter();
  const prependPost = useFeedStore((s) => s.prependPost);
  const [content, setContent] = useState("");
  const [visibility, setVisibility] = useState<PostVisibility>("PUBLIC");
  const [previews, setPreviews] = useState<PreviewItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState<"idle" | "uploading" | "processing">("idle");

  const remaining = 5000 - content.length;
  const canSubmit = useMemo(() => {
    if (uploading) return false;
    if (content.trim().length === 0 && previews.length === 0) return false;
    if (content.length > 5000) return false;
    return true;
  }, [content, previews.length, uploading]);

  function addFiles(fileList: FileList | null) {
    if (!fileList?.length) return;
    const next: PreviewItem[] = [];
    for (const file of Array.from(fileList)) {
      if (previews.length + next.length >= MEDIA_LIMITS.maxFiles) {
        toast.error(`At most ${MEDIA_LIMITS.maxFiles} files.`);
        break;
      }
      const kind = uploadMediaHint(file);
      if (kind === "unknown") {
        toast.error(`Unsupported file: ${file.name}`);
        continue;
      }
      if (kind === "image" && file.size > MEDIA_LIMITS.imageMaxBytes) {
        toast.error("Images must be 10 MB or smaller.");
        continue;
      }
      if (kind === "video" && file.size > MEDIA_LIMITS.videoMaxBytes) {
        toast.error("Videos must be 200 MB or smaller.");
        continue;
      }
      next.push({
        id: `${file.name}-${file.size}-${file.lastModified}-${Math.random()}`,
        file,
        kind,
        url: URL.createObjectURL(file),
      });
    }
    if (next.length) setPreviews((prev) => [...prev, ...next]);
  }

  function removePreview(id: string) {
    setPreviews((prev) => {
      const target = prev.find((p) => p.id === id);
      if (target) URL.revokeObjectURL(target.url);
      return prev.filter((p) => p.id !== id);
    });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setUploading(true);
    setPhase("uploading");
    setProgress(0);
    try {
      const post = await createPost({
        content: content.trim(),
        visibility,
        media: previews.map((p) => p.file),
        onUploadProgress: (pct) => {
          setProgress(pct);
          if (pct >= 100) setPhase("processing");
        },
      });
      prependPost(post);
      toast.success("Post published");
      previews.forEach((p) => URL.revokeObjectURL(p.url));
      router.push("/home");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not create post"));
      setPhase("idle");
    } finally {
      setUploading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto w-full max-w-2xl space-y-6">
      <div>
        <label htmlFor="post-content" className="sr-only">
          Post content
        </label>
        <textarea
          id="post-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Share an update with your network…"
          rows={6}
          className="w-full resize-y rounded-xl border border-border bg-card/80 px-4 py-3 text-[15px] leading-relaxed outline-none ring-ring focus:ring-2"
          maxLength={5000}
          disabled={uploading}
        />
        <div className="mt-1.5 flex items-center justify-between text-xs text-muted-foreground">
          <span>{remaining} characters left</span>
          <select
            value={visibility}
            onChange={(e) => setVisibility(e.target.value as PostVisibility)}
            disabled={uploading}
            className="rounded-md border border-border bg-background px-2 py-1"
            aria-label="Visibility"
          >
            <option value="PUBLIC">Public</option>
            <option value="PRIVATE">Private</option>
          </select>
        </div>
      </div>

      {previews.length > 0 ? (
        <ul className="grid gap-3 sm:grid-cols-2">
          {previews.map((item) => (
            <li
              key={item.id}
              className="relative overflow-hidden rounded-xl border border-border/70 bg-muted/30"
            >
              {item.kind === "image" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={item.url} alt="" className="aspect-video w-full object-cover" />
              ) : (
                <video src={item.url} className="aspect-video w-full object-cover" controls />
              )}
              <button
                type="button"
                onClick={() => removePreview(item.id)}
                disabled={uploading}
                className="absolute right-2 top-2 rounded-md bg-background/90 p-1.5 text-foreground shadow-sm"
                aria-label="Remove media"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {phase !== "idle" ? (
        <UploadProgress
          percent={progress}
          label={
            phase === "processing" || progress >= 100
              ? previews.some((p) => p.kind === "video")
                ? "Processing video…"
                : "Finishing upload…"
              : `Uploading ${progress}%`
          }
        />
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-4">
        <div className="flex gap-2">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted">
            <ImagePlus className="h-4 w-4" />
            Image
            <input
              type="file"
              accept={MEDIA_LIMITS.imageAccept}
              multiple
              className="hidden"
              disabled={uploading}
              onChange={(e) => {
                addFiles(e.target.files);
                e.target.value = "";
              }}
            />
          </label>
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted">
            <Video className="h-4 w-4" />
            Video
            <input
              type="file"
              accept={MEDIA_LIMITS.videoAccept}
              multiple
              className="hidden"
              disabled={uploading}
              onChange={(e) => {
                addFiles(e.target.files);
                e.target.value = "";
              }}
            />
          </label>
        </div>
        <Button type="submit" disabled={!canSubmit} size="lg">
          {uploading ? "Publishing…" : "Publish"}
        </Button>
      </div>
    </form>
  );
}
