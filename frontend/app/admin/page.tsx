"use client";

import { useEffect } from "react";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin/AdminHeader";
import { SimpleTrendChart } from "@/components/admin/SimpleTrendChart";
import { StatsCard } from "@/components/admin/StatsCard";
import { getApiErrorMessage } from "@/services/api";
import { useAdminStore } from "@/stores/adminStore";

export default function AdminDashboardPage() {
  const overview = useAdminStore((s) => s.overview);
  const trends = useAdminStore((s) => s.trends);
  const loadOverview = useAdminStore((s) => s.loadOverview);
  const loadAnalytics = useAdminStore((s) => s.loadAnalytics);

  useEffect(() => {
    Promise.all([loadOverview(), loadAnalytics()]).catch((err) => {
      toast.error(getApiErrorMessage(err, "Could not load dashboard"));
    });
  }, [loadOverview, loadAnalytics]);

  return (
    <div>
      <AdminHeader
        title="Dashboard"
        description="Platform health and operational overview."
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatsCard label="Total Users" value={overview?.users.total ?? 0} />
        <StatsCard
          label="Active Today"
          value={overview?.users.active_today ?? 0}
          hint="Distinct logins today"
        />
        <StatsCard label="Posts" value={overview?.content.posts ?? 0} />
        <StatsCard label="Comments" value={overview?.content.comments ?? 0} />
        <StatsCard label="Connections" value={overview?.network.connections ?? 0} />
        <StatsCard
          label="Pending Reports"
          value={overview?.reports.pending ?? 0}
          hint="Needs review"
        />
      </div>

      <div className="mt-8 grid gap-4 lg:grid-cols-3">
        <SimpleTrendChart title="User growth" data={trends?.user_growth ?? []} />
        <SimpleTrendChart title="Content growth" data={trends?.content_growth ?? []} />
        <SimpleTrendChart title="Reports trend" data={trends?.reports_trend ?? []} />
      </div>
    </div>
  );
}
