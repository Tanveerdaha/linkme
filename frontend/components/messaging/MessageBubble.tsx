"use client";

import { Download, ExternalLink, FileText } from "lucide-react";

import { ImageAttachment } from "@/components/messaging/ImageAttachment";
import { ReadReceipt } from "@/components/messaging/ReadReceipt";
import { VoicePlayer } from "@/components/messaging/VoicePlayer";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/messaging";

type MessageBubbleProps = {
  message: ChatMessage;
  isOwn: boolean;
};

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function isProbablyUrl(text: string) {
  return /^https?:\/\//i.test(text.trim());
}

export function MessageBubble({ message, isOwn }: MessageBubbleProps) {
  if (message.is_deleted) {
    return (
      <div className={cn("flex", isOwn ? "justify-end" : "justify-start")}>
        <div className="max-w-[75%] rounded-2xl border border-dashed border-border/70 px-3 py-2 text-sm italic text-muted-foreground">
          Message deleted
        </div>
      </div>
    );
  }

  const type = message.message_type || "TEXT";
  const meta = message.metadata || {};
  const filename = (meta.filename as string) || "File";
  const linkUrl = (meta.url as string) || message.content;

  return (
    <div
      className={cn(
        "animate-fade-up flex",
        isOwn ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "max-w-[75%] space-y-1.5 rounded-2xl px-3.5 py-2 text-sm shadow-sm",
          isOwn
            ? "rounded-br-md bg-primary text-primary-foreground"
            : "rounded-bl-md border border-border/60 bg-card",
        )}
      >
        {type === "IMAGE" && message.attachment ? (
          <ImageAttachment src={message.attachment} />
        ) : null}

        {type === "VIDEO" && message.attachment ? (
          <video
            src={message.attachment}
            controls
            playsInline
            className="max-h-64 w-full rounded-lg bg-black"
          />
        ) : null}

        {type === "VOICE" && message.attachment ? (
          <VoicePlayer
            src={message.attachment}
            durationSeconds={Number(meta.duration_seconds) || 0}
            light={isOwn}
          />
        ) : null}

        {type === "FILE" && message.attachment ? (
          <a
            href={message.attachment}
            target="_blank"
            rel="noreferrer"
            className={cn(
              "flex items-center gap-2 rounded-lg px-2 py-1.5",
              isOwn ? "bg-primary-foreground/15" : "bg-muted/50",
            )}
          >
            <FileText className="h-5 w-5 shrink-0" />
            <span className="min-w-0 flex-1 truncate font-medium">{filename}</span>
            <Download className="h-4 w-4 shrink-0 opacity-80" />
          </a>
        ) : null}

        {type === "LINK" ? (
          <a
            href={linkUrl}
            target="_blank"
            rel="noreferrer"
            className={cn(
              "block rounded-lg px-2 py-1.5",
              isOwn ? "bg-primary-foreground/15" : "bg-muted/50",
            )}
          >
            <span className="inline-flex items-center gap-1.5 text-xs font-medium opacity-80">
              <ExternalLink className="h-3.5 w-3.5" />
              Link
            </span>
            <p className="mt-0.5 break-all underline-offset-2 hover:underline">
              {linkUrl}
            </p>
          </a>
        ) : null}

        {type === "TEXT" && message.content ? (
          isProbablyUrl(message.content) ? (
            <a
              href={message.content.trim()}
              target="_blank"
              rel="noreferrer"
              className="break-all underline-offset-2 hover:underline"
            >
              {message.content}
            </a>
          ) : (
            <p className="whitespace-pre-wrap break-words leading-relaxed">
              {message.content}
            </p>
          )
        ) : null}

        {type !== "TEXT" &&
        type !== "LINK" &&
        message.content &&
        message.content !== filename &&
        message.content !== linkUrl ? (
          <p className="whitespace-pre-wrap break-words leading-relaxed">
            {message.content}
          </p>
        ) : null}

        <div
          className={cn(
            "flex items-center gap-1 text-[11px]",
            isOwn ? "justify-end text-primary-foreground/80" : "text-muted-foreground",
          )}
        >
          <span>{formatTime(message.created_at)}</span>
          {isOwn ? (
            <ReadReceipt
              status={message.status}
              className={
                message.status === "READ"
                  ? "text-primary-foreground"
                  : "text-primary-foreground/70"
              }
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}
