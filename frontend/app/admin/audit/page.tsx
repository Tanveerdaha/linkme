"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin/AdminHeader";
import { AdminTable } from "@/components/admin/AdminTable";
import { FilterBar } from "@/components/admin/FilterBar";
import { getApiErrorMessage } from "@/services/api";
import { useAdminStore } from "@/stores/adminStore";

export default function AdminAuditPage() {
  const auditLogs = useAdminStore((s) => s.auditLogs);
  const loading = useAdminStore((s) => s.loading);
  const loadAudit = useAdminStore((s) => s.loadAudit);
  const [filters, setFilters] = useState<Record<string, string>>({});

  useEffect(() => {
    loadAudit().catch((err) =>
      toast.error(getApiErrorMessage(err, "Failed to load audit logs")),
    );
  }, [loadAudit]);

  return (
    <div>
      <AdminHeader
        title="Audit log"
        description="Immutable history of security-sensitive actions."
      />
      <FilterBar
        values={filters}
        onChange={(k, v) => setFilters((f) => ({ ...f, [k]: v }))}
        onApply={() => loadAudit(filters)}
        onClear={() => {
          setFilters({});
          loadAudit({});
        }}
        fields={[
          { key: "user", label: "User", placeholder: "username" },
          {
            key: "action",
            label: "Action",
            type: "select",
            options: [
              { value: "LOGIN", label: "Login" },
              { value: "LOGOUT", label: "Logout" },
              { value: "MODERATION_ACTION", label: "Moderation" },
              { value: "ACCOUNT_DELETE", label: "Account delete" },
              { value: "REPORT_CREATED", label: "Report created" },
              { value: "DATA_EXPORT", label: "Data export" },
            ],
          },
          { key: "object_type", label: "Object type", placeholder: "user / post / report" },
        ]}
      />
      <AdminTable
        loading={loading}
        rows={auditLogs}
        rowKey={(a) => a.id}
        columns={[
          {
            key: "user",
            header: "User",
            render: (a) => a.user || "—",
          },
          {
            key: "action",
            header: "Action",
            render: (a) => a.action,
          },
          {
            key: "object",
            header: "Object",
            render: (a) =>
              a.object_type ? `${a.object_type}:${a.object || a.object_id}` : "—",
          },
          {
            key: "time",
            header: "Time",
            render: (a) => new Date(a.time || a.created_at).toLocaleString(),
          },
        ]}
      />
    </div>
  );
}
