"use client";

import type { Report } from "@/types/moderation";
import { REPORT_REASON_LABELS } from "@/types/moderation";

type ReportDetailProps = {
  report: Report;
};

export function ReportDetail({ report }: ReportDetailProps) {
  return (
    <div className="space-y-3 rounded-xl border border-border/60 p-4">
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">Reason</p>
        <p className="font-medium">{REPORT_REASON_LABELS[report.reason]}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Content</p>
          <p className="text-sm">
            {report.content_type_label} · {report.object_id}
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">User</p>
          <p className="text-sm">
            {report.reported_username ? `@${report.reported_username}` : "—"}
          </p>
        </div>
      </div>
      {report.description ? (
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Description</p>
          <p className="text-sm leading-relaxed text-foreground/85">{report.description}</p>
        </div>
      ) : null}
      <div>
        <p className="text-xs uppercase tracking-wide text-muted-foreground">Status</p>
        <p className="text-sm">{report.status}</p>
      </div>
    </div>
  );
}
