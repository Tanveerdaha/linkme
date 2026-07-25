"use client";

import { Button } from "@/components/ui/button";
import { Modal, ModalContent } from "@/components/ui/modal";

type RemoveConnectionModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  name: string;
  username: string;
  pending?: boolean;
  onConfirm: () => void;
};

export function RemoveConnectionModal({
  open,
  onOpenChange,
  name,
  username,
  pending,
  onConfirm,
}: RemoveConnectionModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent
        title="Remove connection?"
        description={`You will no longer be connected with ${name || `@${username}`}.`}
      >
        <div className="mt-6 flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={pending}
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={pending}
            onClick={onConfirm}
          >
            Remove
          </Button>
        </div>
      </ModalContent>
    </Modal>
  );
}
