"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin/AdminHeader";
import { AdminTable } from "@/components/admin/AdminTable";
import { FilterBar } from "@/components/admin/FilterBar";
import { ReportDetail } from "@/components/admin/ReportDetail";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import * as adminApi from "@/services/admin";
import { useAdminStore } from "@/stores/adminStore";
import type { AdminReport } from "@/types/admin";
import { REPORT_REASON_LABELS, type ReportReason } from "@/types/moderation";

export default function AdminReportsPage() {
  const reports = useAdminStore((s) => s.reports);
  const loading = useAdminStore((s) => s.loading);
  const loadReports = useAdminStore((s) => s.loadReports);
  const [filters, setFilters] = useState<Record<string, string>>({
    status: "PENDING",
  });
  const [selected, setSelected] = useState<AdminReport | null>(null);

  useEffect(() => {
    loadReports(filters).catch((err) =>
      toast.error(getApiErrorMessage(err, "Failed to load reports")),
    );
  }, [loadReports]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleUpdate(report: AdminReport, status: string) {
    try {
      await adminApi.updateReport(report.id, { status });
      toast.success(`Report ${status.toLowerCase()}`);
      setSelected(null);
      await loadReports(filters);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Update failed"));
    }
  }

  return (
    <div>
      <AdminHeader title="Reports" description="Review and resolve community reports." />
      <FilterBar
        values={filters}
        onChange={(k, v) => setFilters((f) => ({ ...f, [k]: v }))}
        onApply={() => loadReports(filters)}
        onClear={() => {
          setFilters({});
          loadReports({});
        }}
        fields={[
          {
            key: "status",
            label: "Status",
            type: "select",
            options: [
              { value: "PENDING", label: "Pending" },
              { value: "UNDER_REVIEW", label: "Under review" },
              { value: "RESOLVED", label: "Resolved" },
              { value: "REJECTED", label: "Rejected" },
            ],
          },
          {
            key: "reason",
            label: "Reason",
            type: "select",
            options: Object.entries(REPORT_REASON_LABELS).map(([value, label]) => ({
              value,
              label,
            })),
          },
          {
            key: "content_type",
            label: "Type",
            type: "select",
            options: [
              { value: "USER", label: "User" },
              { value: "POST", label: "Post" },
              { value: "COMMENT", label: "Comment" },
              { value: "MESSAGE", label: "Message" },
            ],
          },
        ]}
      />

      <AdminTable
        loading={loading}
        rows={reports}
        rowKey={(r) => r.id}
        columns={[
          {
            key: "reason",
            header: "Report",
            render: (r) =>
              REPORT_REASON_LABELS[r.reason as ReportReason] || r.reason,
          },
          {
            key: "reporter",
            header: "Reporter",
            render: (r) => `@${r.reporter}`,
          },
          {
            key: "target",
            header: "Target",
            render: (r) => r.target,
          },
          {
            key: "status",
            header: "Status",
            render: (r) => r.status,
          },
          {
            key: "created",
            header: "Created",
            render: (r) => new Date(r.created_at).toLocaleDateString(),
          },
          {
            key: "actions",
            header: "Actions",
            render: (r) => (
              <div className="flex flex-wrap gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    const detail = await adminApi.getReport(r.id);
                    setSelected(detail);
                  }}
                >
                  Review
                </Button>
                <Button size="sm" variant="outline" onClick={() => handleUpdate(r, "RESOLVE")}>
                  Resolve
                </Button>
                <Button size="sm" variant="ghost" onClick={() => handleUpdate(r, "REJECT")}>
                  Reject
                </Button>
              </div>
            ),
          },
        ]}
      />

      {selected ? (
        <section className="mt-6 space-y-3">
          <h2 className="text-lg font-semibold">Report detail</h2>
          <ReportDetail
            report={{
              id: selected.id,
              content_type_label: selected.content_type_label as never,
              object_id: selected.object_id,
              reason: selected.reason as never,
              description: selected.description,
              status: selected.status as never,
              reported_username: selected.reported_user,
              created_at: selected.created_at,
              updated_at: selected.updated_at,
            }}
          />
          <div className="flex gap-2">
            <Button onClick={() => handleUpdate(selected, "ASSIGN")}>Assign / Review</Button>
            <Button variant="outline" onClick={() => handleUpdate(selected, "RESOLVE")}>
              Resolve
            </Button>
            <Button variant="ghost" onClick={() => handleUpdate(selected, "REJECT")}>
              Reject
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
