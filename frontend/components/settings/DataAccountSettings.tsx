"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { SettingsSection } from "@/components/settings/SettingsSection";
import { Button } from "@/components/ui/button";
import { Modal, ModalContent } from "@/components/ui/modal";
import { getApiErrorMessage } from "@/services/api";
import * as accountApi from "@/services/account";
import { useAuthStore } from "@/stores/authStore";
import type { DataExportStatus } from "@/types/moderation";

export function DataAccountSettings({
  mode = "download",
}: {
  mode?: "download" | "delete";
}) {
  const router = useRouter();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const [exportStatus, setExportStatus] = useState<DataExportStatus | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    accountApi
      .getDataExportStatus()
      .then(setExportStatus)
      .catch(() => {
        /* no export yet */
      });
  }, []);

  async function handleExport() {
    setBusy(true);
    try {
      await accountApi.requestDataExport();
      toast.success("Export started. Refresh in a moment for the download link.");
      const latest = await accountApi.getDataExportStatus();
      setExportStatus(latest);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not start export"));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    try {
      const result = await accountApi.deleteAccount();
      toast.success(result.message);
      clearAuth();
      router.push("/login");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not delete account"));
    } finally {
      setBusy(false);
      setDeleteOpen(false);
    }
  }

  if (mode === "download") {
    return (
      <SettingsSection
        title="Download Your Data"
        description="Request a copy of your LinkMe information."
      >
        <p className="mb-4 text-sm text-muted-foreground">
          Download your posts, comments, profile and connections.
        </p>
        <Button onClick={() => void handleExport()} disabled={busy} variant="outline">
          {busy ? "Requesting…" : "Request download"}
        </Button>
        {exportStatus ? (
          <div className="mt-4 text-sm text-muted-foreground">
            <p>Status: {exportStatus.status}</p>
            {exportStatus.download_url ? (
              <a
                className="text-primary underline"
                href={exportStatus.download_url}
                target="_blank"
                rel="noreferrer"
              >
                Download ZIP
              </a>
            ) : null}
          </div>
        ) : null}
      </SettingsSection>
    );
  }

  return (
    <>
      <SettingsSection
        title="Delete Account"
        description="Deleting your account will remove access."
        className="border-destructive/25"
      >
        <p className="mb-4 text-sm text-muted-foreground">
          Soft-deletes your account. You can restore within 30 days.
        </p>
        <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
          Delete account
        </Button>
      </SettingsSection>

      <Modal open={deleteOpen} onOpenChange={setDeleteOpen}>
        <ModalContent
          title="Delete your account?"
          description="Your profile will be hidden and you will be signed out. You can restore within 30 days."
        >
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={busy}
              onClick={() => void handleDelete()}
            >
              {busy ? "Deleting…" : "Delete Account"}
            </Button>
          </div>
        </ModalContent>
      </Modal>
    </>
  );
}
