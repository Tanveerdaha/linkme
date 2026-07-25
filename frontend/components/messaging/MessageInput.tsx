"use client";

import { useEffect, useRef, useState } from "react";
import { Link2, Loader2, Mic, Paperclip, Send } from "lucide-react";
import { toast } from "sonner";

import { LinkPreview } from "@/components/messaging/LinkPreview";
import {
  inferClientMessageType,
  mediaAcceptAttribute,
  MediaPickerPreview,
} from "@/components/messaging/MediaPicker";
import { useVoiceRecorder } from "@/components/messaging/VoiceRecorder";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { SendMessagePayload } from "@/types/messaging";

type MessageInputProps = {
  onSend: (payload: SendMessagePayload) => Promise<void> | void;
  onTypingStart?: () => void;
  onTypingStop?: () => void;
  disabled?: boolean;
  className?: string;
};

type Mode = "idle" | "link";

export function MessageInput({
  onSend,
  onTypingStart,
  onTypingStop,
  disabled,
  className,
}: MessageInputProps) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<Mode>("idle");
  const [sending, setSending] = useState(false);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const {
    recordingState,
    elapsedLabel,
    error: voiceError,
    start: startRecording,
    cancel: cancelRecording,
    finishAndGetFile,
    resetIdle: resetVoiceIdle,
  } = useVoiceRecorder();

  const isRecording = recordingState === "recording";
  const isVoiceSending = recordingState === "sending";
  const voiceBusy = isRecording || isVoiceSending;

  useEffect(() => {
    return () => {
      if (typingTimer.current) clearTimeout(typingTimer.current);
      onTypingStop?.();
    };
  }, [onTypingStop]);

  useEffect(() => {
    if (voiceError) toast.error(voiceError);
  }, [voiceError]);

  const handleChange = (value: string) => {
    setText(value);
    onTypingStart?.();
    if (typingTimer.current) clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => onTypingStop?.(), 1200);
  };

  async function submitPayload(payload: SendMessagePayload) {
    setSending(true);
    try {
      await onSend(payload);
      setText("");
      setFile(null);
      setMode("idle");
      onTypingStop?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not send message");
      throw err;
    } finally {
      setSending(false);
    }
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (sending || disabled || voiceBusy) return;

    if (file) {
      const message_type = inferClientMessageType(file);
      await submitPayload({
        content: text.trim(),
        attachment: file,
        message_type,
        metadata: { filename: file.name },
      });
      return;
    }

    const content = text.trim();
    if (!content) return;
    await submitPayload({ content, message_type: "TEXT" });
  };

  async function handleMicClick() {
    if (disabled || sending || voiceBusy) return;
    setFile(null);
    setMode("idle");
    await startRecording();
  }

  async function handleVoiceSend() {
    if (disabled || !isRecording) return;
    try {
      const result = await finishAndGetFile();
      if (!result) {
        resetVoiceIdle();
        return;
      }
      await submitPayload({
        attachment: result.file,
        message_type: "VOICE",
        metadata: {
          filename: result.file.name,
          duration_seconds: result.durationSeconds,
        },
      });
      resetVoiceIdle();
    } catch {
      resetVoiceIdle();
    }
  }

  function handleVoiceCancel() {
    cancelRecording();
  }

  const showTextSend = Boolean(text.trim() || file) && !voiceBusy;

  return (
    <form
      onSubmit={(e) => void handleSubmit(e)}
      className={cn(
        "border-t border-border/70 bg-card/90 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur-sm",
        className,
      )}
    >
      {mode === "link" && !voiceBusy ? (
        <LinkPreview
          disabled={disabled || sending}
          onCancel={() => setMode("idle")}
          onSend={async (url) => {
            await submitPayload({
              content: url,
              message_type: "LINK",
              metadata: { url },
            });
          }}
        />
      ) : null}

      {mode === "idle" && file && !voiceBusy ? (
        <MediaPickerPreview
          file={file}
          sending={sending}
          onCancel={() => setFile(null)}
          onSend={() => void handleSubmit()}
        />
      ) : null}

      {(mode === "idle" || voiceBusy) && !(mode === "idle" && file && !voiceBusy) ? (
        <div className="flex items-end gap-1.5 sm:gap-2">
          <input
            ref={fileRef}
            type="file"
            accept={mediaAcceptAttribute()}
            className="hidden"
            onChange={(e) => {
              const next = e.target.files?.[0] || null;
              setFile(next);
              e.target.value = "";
            }}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0"
            disabled={disabled || sending || voiceBusy}
            onClick={() => fileRef.current?.click()}
            aria-label="Attach media"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0"
            disabled={disabled || sending || voiceBusy}
            onClick={() => {
              setFile(null);
              setMode("link");
            }}
            aria-label="Share link"
          >
            <Link2 className="h-4 w-4" />
          </Button>

          {voiceBusy ? (
            <div className="flex min-h-10 min-w-0 flex-1 items-center gap-2 rounded-xl border border-border/70 bg-background px-3 py-2 text-sm">
              <span className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-destructive" />
              <span className="min-w-0 flex-1 truncate font-medium text-destructive">
                {isVoiceSending ? "Sending…" : "Recording..."}
              </span>
              <span className="shrink-0 tabular-nums text-foreground">
                {elapsedLabel}
              </span>
              {!isVoiceSending ? (
                <button
                  type="button"
                  onClick={handleVoiceCancel}
                  className="shrink-0 text-xs font-medium text-muted-foreground hover:text-foreground"
                >
                  Cancel
                </button>
              ) : null}
            </div>
          ) : (
            <textarea
              value={text}
              onChange={(e) => handleChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void handleSubmit();
                }
              }}
              rows={1}
              placeholder="Type message..."
              disabled={disabled || sending}
              className="max-h-32 min-h-10 flex-1 resize-none rounded-xl border border-border/70 bg-background px-3 py-2.5 text-sm outline-none ring-ring focus:ring-2"
            />
          )}

          {isRecording ? (
            <Button
              type="button"
              size="icon"
              className="shrink-0"
              disabled={disabled}
              onClick={() => void handleVoiceSend()}
              aria-label="Send voice message"
            >
              <Send className="h-4 w-4" />
            </Button>
          ) : isVoiceSending ? (
            <Button type="button" size="icon" className="shrink-0" disabled aria-label="Sending">
              <Loader2 className="h-4 w-4 animate-spin" />
            </Button>
          ) : showTextSend ? (
            <Button
              type="submit"
              size="icon"
              className="shrink-0"
              disabled={disabled || sending}
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="shrink-0"
              disabled={disabled || sending}
              onClick={() => void handleMicClick()}
              aria-label="Record voice message"
            >
              <Mic className="h-4 w-4" />
            </Button>
          )}
        </div>
      ) : null}
    </form>
  );
}
