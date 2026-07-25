"use client";

import { useEffect } from "react";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin/AdminHeader";
import { AdminTable } from "@/components/admin/AdminTable";
import { getApiErrorMessage } from "@/services/api";
import { useAdminStore } from "@/stores/adminStore";

export default function AdminModerationPage() {
  const moderation = useAdminStore((s) => s.moderation);
  const loading = useAdminStore((s) => s.loading);
  const loadModeration = useAdminStore((s) => s.loadModeration);

  useEffect(() => {
    loadModeration().catch((err) =>
      toast.error(getApiErrorMessage(err, "Failed to load moderation history")),
    );
  }, [loadModeration]);

  return (
    <div>
      <AdminHeader
        title="Moderation history"
        description="Actions taken by staff across the platform."
      />
      <AdminTable
        loading={loading}
        rows={moderation}
        rowKey={(m) => m.id}
        columns={[
          {
            key: "admin",
            header: "Admin",
            render: (m) => m.admin || "—",
          },
          {
            key: "action",
            header: "Action",
            render: (m) => (
              <span className="rounded-md bg-muted px-2 py-0.5 text-xs">{m.action}</span>
            ),
          },
          {
            key: "target",
            header: "Target",
            render: (m) => `${m.target_type}:${m.target_id}`,
          },
          {
            key: "reason",
            header: "Reason",
            render: (m) => (
              <span className="max-w-xs truncate text-muted-foreground">{m.reason || "—"}</span>
            ),
          },
          {
            key: "date",
            header: "Date",
            render: (m) => new Date(m.date || m.created_at).toLocaleString(),
          },
        ]}
      />
    </div>
  );
}
