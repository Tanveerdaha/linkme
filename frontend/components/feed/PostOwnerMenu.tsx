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
import { deletePost } from "@/services/posts";
import { useFeedStore } from "@/stores/feedStore";
import type { Post } from "@/types";

type PostOwnerMenuProps = {
  post: Post;
};

export function PostOwnerMenu({ post }: PostOwnerMenuProps) {
  const router = useRouter();
  const removePost = useFeedStore((s) => s.removePost);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

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
          <DropdownItem onSelect={() => router.push(`/post/${post.id}/edit`)}>
            Edit post
          </DropdownItem>
          <DropdownSeparator />
          <DropdownItem
            className="text-destructive focus:text-destructive"
            onSelect={() => setDeleteOpen(true)}
          >
            Delete post
          </DropdownItem>
        </DropdownContent>
      </Dropdown>

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
