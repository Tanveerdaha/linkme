"use client";

import { useMemo } from "react";
import { FileText, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { MessageType } from "@/types/messaging";

const ACCEPT =
  "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp,video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov,application/pdf,.pdf,.doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

export function mediaAcceptAttribute() {
  return ACCEPT;
}

export function inferClientMessageType(file: File): MessageType {
  const type = file.type.toLowerCase();
  const name = file.name.toLowerCase();
  if (type.startsWith("image/") || /\.(jpe?g|png|webp)$/.test(name)) return "IMAGE";
  if (type.startsWith("video/") || /\.(mp4|webm|mov)$/.test(name)) return "VIDEO";
  if (type.startsWith("audio/") || /\.(webm|mp4|m4a|ogg|mp3)$/.test(name)) return "VOICE";
  return "FILE";
}

type MediaPickerPreviewProps = {
  file: File;
  onCancel: () => void;
  onSend: () => void;
  sending?: boolean;
};

export function MediaPickerPreview({
  file,
  onCancel,
  onSend,
  sending,
}: MediaPickerPreviewProps) {
  const kind = inferClientMessageType(file);
  const previewUrl = useMemo(() => {
    if (kind === "IMAGE" || kind === "VIDEO") return URL.createObjectURL(file);
    return null;
  }, [file, kind]);

  return (
    <div className="mb-2 space-y-2 rounded-xl border border-border/60 bg-muted/30 p-3">
      {kind === "IMAGE" && previewUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={previewUrl}
          alt={file.name}
          className="max-h-48 w-full rounded-lg object-cover"
        />
      ) : null}
      {kind === "VIDEO" && previewUrl ? (
        <video src={previewUrl} controls className="max-h-48 w-full rounded-lg bg-black" />
      ) : null}
      {kind === "FILE" ? (
        <div className="flex items-center gap-2 text-sm">
          <FileText className="h-5 w-5 text-primary" />
          <span className="truncate font-medium">{file.name}</span>
        </div>
      ) : (
        <p className="truncate text-xs text-muted-foreground">{file.name}</p>
      )}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={sending}>
          <X className="mr-1 h-3.5 w-3.5" />
          Cancel
        </Button>
        <Button type="button" size="sm" onClick={onSend} disabled={sending}>
          {sending ? "Sending…" : "Send"}
        </Button>
      </div>
    </div>
  );
}
