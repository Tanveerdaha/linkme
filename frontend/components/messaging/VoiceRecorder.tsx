"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type RecordingState = "idle" | "recording" | "sending";

function formatElapsed(ms: number) {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

/**
 * Shared MediaRecorder lifecycle for voice messages.
 * Preserves existing upload/send flow; only manages capture state.
 */
export function useVoiceRecorder() {
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const startedAt = useRef(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      stopTracks();
      if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
        mediaRecorder.current.onstop = null;
        mediaRecorder.current.stop();
      }
    };
  }, [stopTracks]);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      chunks.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunks.current.push(event.data);
      };
      mediaRecorder.current = recorder;
      startedAt.current = Date.now();
      setElapsedMs(0);
      timer.current = setInterval(() => {
        setElapsedMs(Date.now() - startedAt.current);
      }, 250);
      recorder.start();
      setRecordingState("recording");
    } catch {
      setError("Microphone access is required to record voice messages.");
      setRecordingState("idle");
    }
  }, []);

  const cancel = useCallback(() => {
    if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
      mediaRecorder.current.onstop = null;
      mediaRecorder.current.stop();
    }
    stopTracks();
    chunks.current = [];
    setElapsedMs(0);
    setError(null);
    setRecordingState("idle");
  }, [stopTracks]);

  const finishAndGetFile = useCallback(async (): Promise<{
    file: File;
    durationSeconds: number;
  } | null> => {
    const recorder = mediaRecorder.current;
    if (!recorder || recorder.state === "inactive") return null;

    setRecordingState("sending");
    const durationSeconds = Math.max(
      1,
      Math.round((Date.now() - startedAt.current) / 1000),
    );

    await new Promise<void>((resolve) => {
      recorder.onstop = () => resolve();
      recorder.stop();
    });
    stopTracks();

    const mime = chunks.current[0]?.type || "audio/webm";
    const blob = new Blob(chunks.current, { type: mime });
    const ext = mime.includes("mp4") ? "mp4" : "webm";
    const file = new File([blob], `voice-${Date.now()}.${ext}`, { type: mime });
    chunks.current = [];
    return { file, durationSeconds };
  }, [stopTracks]);

  const resetIdle = useCallback(() => {
    setElapsedMs(0);
    setError(null);
    setRecordingState("idle");
  }, []);

  return {
    recordingState,
    elapsedLabel: formatElapsed(elapsedMs),
    error,
    start,
    cancel,
    finishAndGetFile,
    resetIdle,
  };
}
