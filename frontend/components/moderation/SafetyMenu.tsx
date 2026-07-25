"use client";

import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { toast } from "sonner";

import { ReportModal } from "@/components/moderation/ReportModal";
import { Button } from "@/components/ui/button";
import {
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownSeparator,
  DropdownTrigger,
} from "@/components/ui/dropdown";
import { Modal, ModalContent } from "@/components/ui/modal";
import { getApiErrorMessage } from "@/services/api";
import { blockUser } from "@/services/moderation";
import { useAuthStore } from "@/stores/authStore";
import type { ReportContentType } from "@/types/moderation";

type SafetyMenuProps = {
  contentType: ReportContentType;
  objectId: string;
  username?: string;
  label?: string;
  showBlock?: boolean;
};

export function SafetyMenu({
  contentType,
  objectId,
  username,
  label,
  showBlock = false,
}: SafetyMenuProps) {
  const currentUser = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [reportOpen, setReportOpen] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [blocking, setBlocking] = useState(false);

  if (!isAuthenticated) return null;
  if (username && currentUser?.username === username) return null;

  async function confirmBlock() {
    if (!username) return;
    setBlocking(true);
    try {
      await blockUser(username);
      toast.success(`Blocked @${username}`);
      setBlockOpen(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not block user"));
    } finally {
      setBlocking(false);
    }
  }

  return (
    <>
      <Dropdown>
        <DropdownTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="More actions">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownTrigger>
        <DropdownContent align="end">
          <DropdownItem onSelect={() => setReportOpen(true)}>Report</DropdownItem>
          {showBlock && username ? (
            <>
              <DropdownSeparator />
              <DropdownItem
                className="text-destructive focus:text-destructive"
                onSelect={() => setBlockOpen(true)}
              >
                Block @{username}
              </DropdownItem>
            </>
          ) : null}
        </DropdownContent>
      </Dropdown>

      <ReportModal
        open={reportOpen}
        onOpenChange={setReportOpen}
        contentType={contentType}
        objectId={objectId}
        targetLabel={label}
      />

      <Modal open={blockOpen} onOpenChange={setBlockOpen}>
        <ModalContent
          title="Block user?"
          description="Are you sure? This user will no longer interact with you."
        >
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline" onClick={() => setBlockOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={blocking} onClick={confirmBlock}>
              {blocking ? "Blocking…" : "Block"}
            </Button>
          </div>
        </ModalContent>
      </Modal>
    </>
  );
}
