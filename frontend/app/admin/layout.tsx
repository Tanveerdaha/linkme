"use client";

import { AdminGuard } from "@/components/admin/AdminGuard";
import { AdminSidebar } from "@/components/admin/AdminSidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminGuard>
      <div className="flex min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-muted/40 via-background to-background">
        <AdminSidebar />
        <main className="min-w-0 flex-1 overflow-x-auto px-4 py-6 sm:px-8">{children}</main>
      </div>
    </AdminGuard>
  );
}
