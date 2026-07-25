"use client";

type UploadProgressProps = {
  percent: number;
  label?: string;
};

export function UploadProgress({ percent, label }: UploadProgressProps) {
  const clamped = Math.max(0, Math.min(100, percent));
  return (
    <div className="space-y-2" role="status" aria-live="polite">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{label || (clamped < 100 ? `Uploading ${clamped}%` : "Processing…")}</span>
        <span>{clamped}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-300 ease-out"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
