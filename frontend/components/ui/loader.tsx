import { cn } from "@/lib/utils";

type LoaderProps = {
  className?: string;
  label?: string;
};

/** Inline spinner used for async UI states. */
export function Loader({ className, label = "Loading" }: LoaderProps) {
  return (
    <div className={cn("inline-flex items-center gap-2 text-sm text-muted-foreground", className)} role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-primary" />
      <span>{label}</span>
    </div>
  );
}
