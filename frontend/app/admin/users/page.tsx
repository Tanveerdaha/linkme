"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { AdminHeader } from "@/components/admin/AdminHeader";
import { AdminTable } from "@/components/admin/AdminTable";
import { FilterBar } from "@/components/admin/FilterBar";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Modal, ModalContent } from "@/components/ui/modal";
import { getApiErrorMessage } from "@/services/api";
import * as adminApi from "@/services/admin";
import { useAdminStore } from "@/stores/adminStore";
import type { AdminUser } from "@/types/admin";

export default function AdminUsersPage() {
  const users = useAdminStore((s) => s.users);
  const loading = useAdminStore((s) => s.loading);
  const loadUsers = useAdminStore((s) => s.loadUsers);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [suspendTarget, setSuspendTarget] = useState<AdminUser | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    loadUsers().catch((err) => toast.error(getApiErrorMessage(err, "Failed to load users")));
  }, [loadUsers]);

  async function handleSuspend() {
    if (!suspendTarget) return;
    setBusy(true);
    try {
      await adminApi.suspendUser(suspendTarget.id, {
        reason,
        duration: "7_days",
      });
      toast.success(`Suspended @${suspendTarget.username}`);
      setSuspendTarget(null);
      setReason("");
      await loadUsers(filters);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not suspend user"));
    } finally {
      setBusy(false);
    }
  }

  async function handleUnsuspend(user: AdminUser) {
    try {
      await adminApi.unsuspendUser(user.id);
      toast.success(`Restored @${user.username}`);
      await loadUsers(filters);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not unsuspend"));
    }
  }

  async function handleDelete(user: AdminUser) {
    if (!window.confirm(`Soft-delete @${user.username}?`)) return;
    try {
      await adminApi.deleteUser(user.id, "Admin action");
      toast.success("User deleted");
      await loadUsers(filters);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not delete user"));
    }
  }

  return (
    <div>
      <AdminHeader title="Users" description="Search, suspend, and manage accounts." />
      <FilterBar
        values={filters}
        onChange={(k, v) => setFilters((f) => ({ ...f, [k]: v }))}
        onApply={() =>
          loadUsers(filters).catch((err) =>
            toast.error(getApiErrorMessage(err, "Filter failed")),
          )
        }
        onClear={() => {
          setFilters({});
          loadUsers({}).catch(() => undefined);
        }}
        fields={[
          { key: "search", label: "Search", placeholder: "username or email" },
          {
            key: "status",
            label: "Status",
            type: "select",
            options: [
              { value: "ACTIVE", label: "Active" },
              { value: "SUSPENDED", label: "Suspended" },
              { value: "INACTIVE", label: "Inactive" },
              { value: "DELETED", label: "Deleted" },
            ],
          },
          {
            key: "verified",
            label: "Verified",
            type: "select",
            options: [
              { value: "true", label: "Yes" },
              { value: "false", label: "No" },
            ],
          },
        ]}
      />

      <AdminTable
        loading={loading}
        rows={users}
        rowKey={(u) => u.id}
        columns={[
          {
            key: "user",
            header: "User",
            render: (u) => (
              <div className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  {u.avatar ? <AvatarImage src={u.avatar} alt={u.username} /> : null}
                  <AvatarFallback>{u.username.slice(0, 2).toUpperCase()}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">@{u.username}</p>
                  <p className="text-xs text-muted-foreground">{u.email}</p>
                </div>
              </div>
            ),
          },
          {
            key: "status",
            header: "Status",
            render: (u) => (
              <span className="rounded-md bg-muted px-2 py-0.5 text-xs">{u.status}</span>
            ),
          },
          {
            key: "created",
            header: "Created",
            render: (u) => new Date(u.created_at).toLocaleDateString(),
          },
          {
            key: "actions",
            header: "Actions",
            render: (u) => (
              <div className="flex flex-wrap gap-1">
                <Button asChild size="sm" variant="outline">
                  <Link href={`/admin/users?view=${u.id}`}>View</Link>
                </Button>
                {u.status === "SUSPENDED" ? (
                  <Button size="sm" variant="outline" onClick={() => handleUnsuspend(u)}>
                    Restore
                  </Button>
                ) : (
                  <Button size="sm" variant="outline" onClick={() => setSuspendTarget(u)}>
                    Suspend
                  </Button>
                )}
                <Button size="sm" variant="ghost" onClick={() => handleDelete(u)}>
                  Delete
                </Button>
              </div>
            ),
          },
        ]}
      />

      <Modal open={!!suspendTarget} onOpenChange={(o) => !o && setSuspendTarget(null)}>
        <ModalContent
          title="Suspend user"
          description={
            suspendTarget
              ? `Suspend @${suspendTarget.username} for 7 days.`
              : undefined
          }
        >
          <textarea
            className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            rows={3}
            placeholder="Reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline" onClick={() => setSuspendTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={busy} onClick={handleSuspend}>
              {busy ? "Suspending…" : "Suspend"}
            </Button>
          </div>
        </ModalContent>
      </Modal>
    </div>
  );
}
