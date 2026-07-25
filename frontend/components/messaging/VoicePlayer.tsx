"use client";

import { useEffect, useRef, useState } from "react";
import { Pause, Play } from "lucide-react";

import { cn } from "@/lib/utils";

type VoicePlayerProps = {
  src: string;
  durationSeconds?: number;
  className?: string;
  light?: boolean;
};

function formatDuration(seconds: number) {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}:${rem.toString().padStart(2, "0")}`;
}

export function VoicePlayer({
  src,
  durationSeconds = 0,
  className,
  light,
}: VoicePlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(durationSeconds);

  useEffect(() => {
    const audio = new Audio(src);
    audioRef.current = audio;
    const onTime = () => {
      if (!audio.duration) return;
      setProgress(audio.currentTime / audio.duration);
      setDuration(audio.duration);
    };
    const onEnded = () => {
      setPlaying(false);
      setProgress(0);
    };
    audio.addEventListener("timeupdate", onTime);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("loadedmetadata", () => {
      if (audio.duration && Number.isFinite(audio.duration)) {
        setDuration(audio.duration);
      }
    });
    return () => {
      audio.pause();
      audio.removeEventListener("timeupdate", onTime);
      audio.removeEventListener("ended", onEnded);
      audioRef.current = null;
    };
  }, [src]);

  async function toggle() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }
    await audio.play();
    setPlaying(true);
  }

  return (
    <div className={cn("flex min-w-[180px] items-center gap-2", className)}>
      <button
        type="button"
        onClick={() => void toggle()}
        className={cn(
          "inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          light
            ? "bg-primary-foreground/20 text-primary-foreground"
            : "bg-primary/15 text-primary",
        )}
        aria-label={playing ? "Pause voice message" : "Play voice message"}
      >
        {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
      </button>
      <div className="min-w-0 flex-1">
        <div
          className={cn(
            "h-1 overflow-hidden rounded-full",
            light ? "bg-primary-foreground/25" : "bg-muted",
          )}
        >
          <div
            className={cn(
              "h-full rounded-full transition-[width]",
              light ? "bg-primary-foreground" : "bg-primary",
            )}
            style={{ width: `${Math.min(100, progress * 100)}%` }}
          />
        </div>
        <p
          className={cn(
            "mt-1 text-[11px] tabular-nums",
            light ? "text-primary-foreground/80" : "text-muted-foreground",
          )}
        >
          {formatDuration(duration || durationSeconds)}
        </p>
      </div>
    </div>
  );
}
