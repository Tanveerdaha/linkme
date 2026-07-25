"use client";

type TypingIndicatorProps = {
  username?: string;
};

export function TypingIndicator({ username }: TypingIndicatorProps) {
  if (!username) return null;
  return (
    <div className="animate-fade-up px-4 py-1 text-xs text-muted-foreground">
      <span className="font-medium text-foreground/80">{username}</span> is typing
      <span className="ml-0.5 inline-flex gap-0.5">
        <span className="animate-soft-pulse">.</span>
        <span className="animate-soft-pulse [animation-delay:120ms]">.</span>
        <span className="animate-soft-pulse [animation-delay:240ms]">.</span>
      </span>
    </div>
  );
}
