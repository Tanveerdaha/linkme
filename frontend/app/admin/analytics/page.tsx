"use client";

import { useEffect } from "react";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin/AdminHeader";
import { SimpleTrendChart } from "@/components/admin/SimpleTrendChart";
import { StatsCard } from "@/components/admin/StatsCard";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/services/api";
import * as adminApi from "@/services/admin";
import { useAdminStore } from "@/stores/adminStore";

export default function AdminAnalyticsPage() {
  const metrics = useAdminStore((s) => s.metrics);
  const trends = useAdminStore((s) => s.trends);
  const loadAnalytics = useAdminStore((s) => s.loadAnalytics);
  const hasPermission = useAdminStore((s) => s.hasPermission);

  useEffect(() => {
    loadAnalytics().catch((err) =>
      toast.error(getApiErrorMessage(err, "Failed to load analytics")),
    );
  }, [loadAnalytics]);

  async function handleExport() {
    try {
      const result = await adminApi.requestExport({
        export_type: "USERS",
        format: "CSV",
      });
      toast.success(`Export queued (${result.status})`);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Export failed"));
    }
  }

  return (
    <div>
      <AdminHeader
        title="Analytics"
        description="Daily activity and growth metrics."
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatsCard label="Daily Active Users" value={metrics?.daily_active_users ?? 0} />
        <StatsCard label="New Registrations" value={metrics?.new_registrations ?? 0} />
        <StatsCard label="Posts Created" value={metrics?.posts_created ?? 0} />
        <StatsCard label="Comments" value={metrics?.comments ?? 0} />
        <StatsCard label="Messages" value={metrics?.messages ?? 0} />
        <StatsCard label="Reports" value={metrics?.reports ?? 0} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <SimpleTrendChart title="Registrations (14d)" data={trends?.user_growth ?? []} />
        <SimpleTrendChart title="Posts (14d)" data={trends?.content_growth ?? []} />
        <SimpleTrendChart title="Comments (14d)" data={trends?.comments_trend ?? []} />
        <SimpleTrendChart title="Reports (14d)" data={trends?.reports_trend ?? []} />
      </div>

      {hasPermission("EXPORT_DATA") ? (
        <div className="mt-6">
          <Button variant="outline" onClick={handleExport}>
            Export users CSV
          </Button>
        </div>
      ) : null}
    </div>
  );
}
