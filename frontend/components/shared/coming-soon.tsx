type ComingSoonProps = {
  title: string;
  description?: string;
};

/** Shared placeholder for protected routes until feature phases land. */
export function ComingSoon({ title, description = "This area is scaffolding for a future phase." }: ComingSoonProps) {
  return (
    <main className="mx-auto flex min-h-[70vh] w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 text-center">
      <p className="animate-fade-up font-[family-name:var(--font-fraunces)] text-4xl font-semibold tracking-tight">
        {title}
      </p>
      <p className="animate-fade-up mt-3 max-w-md text-muted-foreground" style={{ animationDelay: "80ms" }}>
        Coming Soon
      </p>
      <p className="animate-fade-up mt-2 text-sm text-muted-foreground" style={{ animationDelay: "140ms" }}>
        {description}
      </p>
    </main>
  );
}
