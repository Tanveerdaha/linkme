"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Modal, ModalContent } from "@/components/ui/modal";
import type { ModerationActionType } from "@/types/moderation";

type ModerationActionModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  targetType: string;
  targetId: string;
  reportId?: string;
  onConfirm: (payload: {
    action: ModerationActionType;
    reason: string;
    suspend_days?: number;
  }) => Promise<void>;
};

const ACTIONS: { value: ModerationActionType; label: string }[] = [
  { value: "WARNING", label: "Warning" },
  { value: "CONTENT_REMOVED", label: "Remove content" },
  { value: "USER_SUSPENDED", label: "Suspend user" },
  { value: "USER_BANNED", label: "Ban user" },
];

export function ModerationActionModal({
  open,
  onOpenChange,
  targetType,
  targetId,
  onConfirm,
}: ModerationActionModalProps) {
  const [action, setAction] = useState<ModerationActionType>("WARNING");
  const [reason, setReason] = useState("");
  const [suspendDays, setSuspendDays] = useState(7);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onConfirm({
        action,
        reason,
        suspend_days: action === "USER_SUSPENDED" ? suspendDays : undefined,
      });
      onOpenChange(false);
      setReason("");
      setAction("WARNING");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent
        title="Moderation action"
        description={`Apply an action to ${targetType} ${targetId}.`}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">Action</legend>
            {ACTIONS.map((a) => (
              <label key={a.value} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="action"
                  checked={action === a.value}
                  onChange={() => setAction(a.value)}
                />
                {a.label}
              </label>
            ))}
          </fieldset>
          {action === "USER_SUSPENDED" ? (
            <div>
              <label className="text-sm font-medium" htmlFor="suspend-days">
                Suspend days
              </label>
              <input
                id="suspend-days"
                type="number"
                min={1}
                max={365}
                className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                value={suspendDays}
                onChange={(e) => setSuspendDays(Number(e.target.value))}
              />
            </div>
          ) : null}
          <div>
            <label className="text-sm font-medium" htmlFor="mod-reason">
              Reason
            </label>
            <textarea
              id="mod-reason"
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Applying…" : "Apply action"}
            </Button>
          </div>
        </form>
      </ModalContent>
    </Modal>
  );
}
