"use client";

import { useRef, useState } from "react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";

type AvatarUploadProps = {
  label: string;
  currentUrl?: string | null;
  onFileChange: (file: File | null) => void;
  previewClassName?: string;
  kind?: "avatar" | "cover";
};

const MAX_BYTES = 5 * 1024 * 1024;
const ALLOWED = ["image/jpeg", "image/png", "image/webp"];

export function AvatarUpload({
  label,
  currentUrl,
  onFileChange,
  kind = "avatar",
}: AvatarUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const display = preview || currentUrl || null;

  const handleChange = (file: File | null) => {
    setError(null);
    if (!file) {
      setPreview(null);
      onFileChange(null);
      return;
    }
    if (!ALLOWED.includes(file.type)) {
      setError("Use jpg, png, or webp");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("Image must be 5 MB or smaller");
      return;
    }
    setPreview(URL.createObjectURL(file));
    onFileChange(file);
  };

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{label}</p>
      <div className="flex items-center gap-4">
        {kind === "avatar" ? (
          <Avatar className="h-20 w-20">
            {display ? <AvatarImage src={display} alt={label} /> : null}
            <AvatarFallback>IMG</AvatarFallback>
          </Avatar>
        ) : (
          <div
            className="h-20 w-36 overflow-hidden rounded-lg border border-border bg-muted"
            style={
              display
                ? { backgroundImage: `url(${display})`, backgroundSize: "cover", backgroundPosition: "center" }
                : undefined
            }
          />
        )}
        <div className="space-y-2">
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(event) => handleChange(event.target.files?.[0] ?? null)}
          />
          <Button type="button" variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
            Choose image
          </Button>
          {preview ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                if (inputRef.current) inputRef.current.value = "";
                handleChange(null);
              }}
            >
              Clear
            </Button>
          ) : null}
        </div>
      </div>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}
