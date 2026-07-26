"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownSeparator,
  DropdownTrigger,
} from "@/components/ui/dropdown";
import { Modal, ModalContent } from "@/components/ui/modal";
import { getApiErrorMessage } from "@/services/api";
import { deletePost, updatePost } from "@/services/posts";
import { useFeedStore } from "@/stores/feedStore";
import type { Post, PostVisibility } from "@/types";

type PostOwnerMenuProps = {
  post: Post;
};

export function PostOwnerMenu({ post }: PostOwnerMenuProps) {
  const router = useRouter();
  const updateStorePost = useFeedStore((s) => s.updatePost);
  const removePost = useFeedStore((s) => s.removePost);

  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [content, setContent] = useState(post.content || "");
  const [visibility, setVisibility] = useState<PostVisibility>(post.visibility);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  function openEdit() {
    setContent(post.content || "");
    setVisibility(post.visibility);
    setEditOpen(true);
  }

  async function handleSave() {
    const trimmed = content.trim();
    if (!trimmed && !(post.media?.length > 0)) {
      toast.error("Post cannot be empty");
      return;
    }
    if (trimmed.length > 5000) {
      toast.error("Posts can be at most 5000 characters");
      return;
    }
    setSaving(true);
    try {
      const updated = await updatePost(post.id, {
        content: trimmed,
        visibility,
      });
      updateStorePost(updated);
      toast.success("Post updated");
      setEditOpen(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not update post"));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deletePost(post.id);
      removePost(post.id);
      toast.success("Post deleted");
      setDeleteOpen(false);
      if (typeof window !== "undefined" && window.location.pathname.startsWith("/post/")) {
        router.push("/home");
      }
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not delete post"));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <>
      <Dropdown>
        <DropdownTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Post options">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownTrigger>
        <DropdownContent align="end">
          <DropdownItem onSelect={openEdit}>Edit post</DropdownItem>
          <DropdownSeparator />
          <DropdownItem
            className="text-destructive focus:text-destructive"
            onSelect={() => setDeleteOpen(true)}
          >
            Delete post
          </DropdownItem>
        </DropdownContent>
      </Dropdown>

      <Modal open={editOpen} onOpenChange={setEditOpen}>
        <ModalContent title="Edit post" description="Update your post content or visibility.">
          <div className="space-y-3">
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={5}
              maxLength={5000}
              className="w-full resize-y rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="What's on your mind?"
            />
            <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
              <label className="flex items-center gap-2">
                <span>Visibility</span>
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value as PostVisibility)}
                  className="rounded-md border border-input bg-background px-2 py-1 text-sm text-foreground"
                >
                  <option value="PUBLIC">Public</option>
                  <option value="CONNECTIONS_ONLY">Connections</option>
                  <option value="PRIVATE">Private</option>
                </select>
              </label>
              <span>{5000 - content.length}</span>
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <Button variant="outline" onClick={() => setEditOpen(false)} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={() => void handleSave()} disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </Button>
            </div>
          </div>
        </ModalContent>
      </Modal>

      <Modal open={deleteOpen} onOpenChange={setDeleteOpen}>
        <ModalContent
          title="Delete post?"
          description="This will remove the post from your profile and feeds. You can’t undo this."
        >
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDeleteOpen(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={deleting}
              onClick={() => void handleDelete()}
            >
              {deleting ? "Deleting…" : "Delete"}
            </Button>
          </div>
        </ModalContent>
      </Modal>
    </>
  );
}
