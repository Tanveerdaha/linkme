"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin/AdminHeader";
import { AdminTable } from "@/components/admin/AdminTable";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import * as adminApi from "@/services/admin";
import { useAdminStore } from "@/stores/adminStore";

export default function AdminContentPage() {
  const posts = useAdminStore((s) => s.posts);
  const comments = useAdminStore((s) => s.comments);
  const loading = useAdminStore((s) => s.loading);
  const loadPosts = useAdminStore((s) => s.loadPosts);
  const loadComments = useAdminStore((s) => s.loadComments);
  const [tab, setTab] = useState<"posts" | "comments">("posts");

  useEffect(() => {
    if (tab === "posts") {
      loadPosts().catch((err) => toast.error(getApiErrorMessage(err, "Failed to load posts")));
    } else {
      loadComments().catch((err) =>
        toast.error(getApiErrorMessage(err, "Failed to load comments")),
      );
    }
  }, [tab, loadPosts, loadComments]);

  return (
    <div>
      <AdminHeader title="Content" description="Review and moderate posts and comments." />
      <div className="mb-4 flex gap-2">
        <Button
          size="sm"
          variant={tab === "posts" ? "default" : "outline"}
          onClick={() => setTab("posts")}
        >
          Posts
        </Button>
        <Button
          size="sm"
          variant={tab === "comments" ? "default" : "outline"}
          onClick={() => setTab("comments")}
        >
          Comments
        </Button>
      </div>

      {tab === "posts" ? (
        <AdminTable
          loading={loading}
          rows={posts}
          rowKey={(p) => p.id}
          columns={[
            {
              key: "author",
              header: "Author",
              render: (p) => <span>@{p.author}</span>,
            },
            {
              key: "content",
              header: "Content",
              render: (p) => (
                <p className="max-w-md truncate text-muted-foreground">{p.content || "(media)"}</p>
              ),
            },
            {
              key: "reports",
              header: "Reports",
              render: (p) => p.reports,
            },
            {
              key: "status",
              header: "Status",
              render: (p) => p.status,
            },
            {
              key: "actions",
              header: "Actions",
              render: (p) => (
                <div className="flex gap-1">
                  {p.status === "DELETED" ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={async () => {
                        try {
                          await adminApi.restorePost(p.id);
                          toast.success("Post restored");
                          await loadPosts();
                        } catch (err) {
                          toast.error(getApiErrorMessage(err, "Restore failed"));
                        }
                      }}
                    >
                      Restore
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={async () => {
                        try {
                          await adminApi.removePost(p.id, "Admin removal");
                          toast.success("Post removed");
                          await loadPosts();
                        } catch (err) {
                          toast.error(getApiErrorMessage(err, "Remove failed"));
                        }
                      }}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ),
            },
          ]}
        />
      ) : (
        <AdminTable
          loading={loading}
          rows={comments}
          rowKey={(c) => c.id}
          columns={[
            {
              key: "author",
              header: "Author",
              render: (c) => <span>@{c.author}</span>,
            },
            {
              key: "content",
              header: "Content",
              render: (c) => <p className="max-w-md truncate">{c.content}</p>,
            },
            {
              key: "status",
              header: "Status",
              render: (c) => c.status,
            },
            {
              key: "actions",
              header: "Actions",
              render: (c) =>
                c.status === "DELETED" ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      await adminApi.restoreComment(c.id);
                      toast.success("Comment restored");
                      await loadComments();
                    }}
                  >
                    Restore
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={async () => {
                      await adminApi.removeComment(c.id, "Admin removal");
                      toast.success("Comment removed");
                      await loadComments();
                    }}
                  >
                    Remove
                  </Button>
                ),
            },
          ]}
        />
      )}
    </div>
  );
}
