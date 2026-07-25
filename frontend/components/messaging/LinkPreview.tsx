"use client";

import { useState } from "react";
import { Link2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type LinkPreviewComposerProps = {
  onCancel: () => void;
  onSend: (url: string) => Promise<void> | void;
  disabled?: boolean;
};

function normalizeUrl(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `https://${trimmed}`;
}

export function LinkPreview({
  onCancel,
  onSend,
  disabled,
}: LinkPreviewComposerProps) {
  const [url, setUrl] = useState("");
  const [sending, setSending] = useState(false);
  const preview = normalizeUrl(url);

  async function handleSend() {
    if (!preview || sending || disabled) return;
    setSending(true);
    try {
      await onSend(preview);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-3 rounded-xl border border-border/60 bg-muted/30 px-3 py-3">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Link2 className="h-4 w-4 text-primary" />
        Paste link
      </div>
      <Input
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com"
        autoFocus
        disabled={disabled || sending}
      />
      {preview ? (
        <div className="rounded-lg border border-border/50 bg-card px-3 py-2 text-xs text-muted-foreground">
          Preview
          <p className="mt-1 truncate font-medium text-foreground">{preview}</p>
        </div>
      ) : null}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={sending}>
          Cancel
        </Button>
        <Button
          type="button"
          size="sm"
          disabled={!preview || sending || disabled}
          onClick={() => void handleSend()}
        >
          {sending ? "Sending…" : "Send"}
        </Button>
      </div>
    </div>
  );
}
