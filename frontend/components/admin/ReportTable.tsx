"use client";

import { Button } from "@/components/ui/button";
import type { Report } from "@/types/moderation";
import { REPORT_REASON_LABELS } from "@/types/moderation";

type ReportTableProps = {
  reports: Report[];
  onReview: (report: Report) => void;
  onResolve: (report: Report) => void;
  onReject: (report: Report) => void;
  loading?: boolean;
};

export function ReportTable({
  reports,
  onReview,
  onResolve,
  onReject,
  loading,
}: ReportTableProps) {
  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading reports…</p>;
  }

  if (reports.length === 0) {
    return <p className="text-sm text-muted-foreground">No pending reports.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border/60">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="border-b border-border/60 bg-muted/30 text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="px-4 py-3 font-medium">Reason</th>
            <th className="px-4 py-3 font-medium">Type</th>
            <th className="px-4 py-3 font-medium">User</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((report) => (
            <tr key={report.id} className="border-b border-border/40 last:border-0">
              <td className="px-4 py-3 font-medium">
                {REPORT_REASON_LABELS[report.reason]} Report
              </td>
              <td className="px-4 py-3 text-muted-foreground">{report.content_type_label}</td>
              <td className="px-4 py-3">
                {report.reported_username ? `@${report.reported_username}` : "—"}
              </td>
              <td className="px-4 py-3">
                <span className="rounded-md bg-muted px-2 py-0.5 text-xs">{report.status}</span>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" onClick={() => onReview(report)}>
                    Review
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => onResolve(report)}>
                    Resolve
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onReject(report)}>
                    Reject
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
