"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Modal, ModalContent } from "@/components/ui/modal";
import { getApiErrorMessage } from "@/services/api";
import { createReport } from "@/services/moderation";
import {
  REPORT_REASON_LABELS,
  type ReportContentType,
  type ReportReason,
} from "@/types/moderation";

type ReportModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contentType: ReportContentType;
  objectId: string;
  targetLabel?: string;
};

const REASONS = Object.keys(REPORT_REASON_LABELS) as ReportReason[];

export function ReportModal({
  open,
  onOpenChange,
  contentType,
  objectId,
  targetLabel,
}: ReportModalProps) {
  const [reason, setReason] = useState<ReportReason>("SPAM");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createReport({
        content_type: contentType,
        object_id: objectId,
        reason,
        description,
      });
      toast.success("Report submitted. Our team will review it.");
      onOpenChange(false);
      setDescription("");
      setReason("SPAM");
    } catch (err) {
      toast.error(getApiErrorMessage(err, "Could not submit report"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent
        title="Report"
        description={
          targetLabel
            ? `Help us understand what's wrong with ${targetLabel}.`
            : "Help us understand the problem."
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">Reason</legend>
            {REASONS.map((r) => (
              <label key={r} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="reason"
                  value={r}
                  checked={reason === r}
                  onChange={() => setReason(r)}
                />
                {REPORT_REASON_LABELS[r]}
              </label>
            ))}
          </fieldset>
          <div>
            <label htmlFor="report-desc" className="text-sm font-medium">
              Description (optional)
            </label>
            <textarea
              id="report-desc"
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
              rows={3}
              maxLength={2000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add context for moderators…"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Submitting…" : "Submit report"}
            </Button>
          </div>
        </form>
      </ModalContent>
    </Modal>
  );
}
