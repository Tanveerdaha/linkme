import {
  MessageCircle,
  Network,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";

const BENEFITS = [
  {
    icon: Users,
    title: "Grow your network",
    description: "Connect with people who share your interests and goals.",
  },
  {
    icon: Sparkles,
    title: "Share what matters",
    description: "Post updates, media, and ideas in a clean professional feed.",
  },
  {
    icon: MessageCircle,
    title: "Real-time messaging",
    description: "Chat instantly with voice, links, and media in one place.",
  },
  {
    icon: ShieldCheck,
    title: "Secure sign-in",
    description: "Email, Google, or WhatsApp OTP. You choose how to join.",
  },
] as const;

type AuthSplitCardProps = {
  children: React.ReactNode;
  className?: string;
  panelTitle?: string;
  panelSubtitle?: string;
};

export function AuthSplitCard({
  children,
  className,
  panelTitle = "Connect. Share. Grow.",
  panelSubtitle = "LinkMe brings your professional network, feed, and conversations together.",
}: AuthSplitCardProps) {
  return (
    <main
      className={cn(
        "relative z-10 mx-auto flex w-full max-w-6xl",
        "min-h-[calc(100dvh-3.5rem)] items-stretch px-0 py-0",
        "sm:items-center sm:px-4 sm:py-8",
        "lg:py-10",
      )}
    >
      <div
        className={cn(
          "grid w-full overflow-hidden bg-card",
          "min-h-[calc(100dvh-3.5rem)] sm:min-h-[min(720px,calc(100dvh-6rem))]",
          "rounded-none border-0 shadow-none",
          "sm:rounded-3xl sm:border sm:border-border/70 sm:shadow-[0_24px_80px_-32px_rgba(15,26,20,0.45)]",
          "lg:grid-cols-[1.05fr_0.95fr]",
          "animate-fade-up",
          className,
        )}
      >
        {/* Mobile compact brand header */}
        <aside className="relative overflow-hidden bg-[linear-gradient(155deg,#0a5f4a_0%,#0d7a5f_48%,#12946f_100%)] px-5 pb-5 pt-5 text-primary-foreground lg:hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute -right-10 -top-12 h-36 w-36 rounded-full bg-white/10 blur-2xl"
          />
          <div className="relative">
            <p className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-medium tracking-wide text-white/90 ring-1 ring-white/15">
              <Network className="h-3 w-3" />
              LinkMe
            </p>
            <h1 className="mt-3 font-[family-name:var(--font-fraunces)] text-2xl font-semibold tracking-tight text-white">
              {panelTitle}
            </h1>
            <p className="mt-1.5 max-w-lg text-sm leading-relaxed text-white/80">
              {panelSubtitle}
            </p>
            <ul className="mt-4 flex gap-2 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {BENEFITS.slice(0, 3).map(({ icon: Icon, title }) => (
                <li
                  key={title}
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-white/12 px-2.5 py-1.5 text-xs font-medium text-white ring-1 ring-white/15"
                >
                  <Icon className="h-3.5 w-3.5 opacity-90" />
                  {title}
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* Desktop benefits panel */}
        <aside className="relative hidden flex-col justify-between overflow-hidden bg-[linear-gradient(155deg,#0a5f4a_0%,#0d7a5f_48%,#12946f_100%)] px-10 py-10 text-primary-foreground lg:flex">
          <div
            aria-hidden
            className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-white/10 blur-2xl"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute -bottom-24 -left-10 h-64 w-64 rounded-full bg-black/10 blur-2xl"
          />
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-[0.12]"
            style={{
              backgroundImage:
                "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.55) 1px, transparent 0)",
              backgroundSize: "22px 22px",
            }}
          />

          <div className="relative">
            <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium tracking-wide text-white/90 ring-1 ring-white/15">
              <Network className="h-3.5 w-3.5" />
              LinkMe
            </p>
            <h1 className="mt-5 font-[family-name:var(--font-fraunces)] text-4xl font-semibold tracking-tight text-white">
              {panelTitle}
            </h1>
            <p className="mt-3 max-w-md text-base leading-relaxed text-white/80">
              {panelSubtitle}
            </p>
          </div>

          <ul className="relative mt-10 space-y-4">
            {BENEFITS.map(({ icon: Icon, title, description }) => (
              <li key={title} className="flex gap-3">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/12 ring-1 ring-white/15">
                  <Icon className="h-4 w-4 text-white" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-white">{title}</p>
                  <p className="mt-0.5 text-sm leading-snug text-white/75">{description}</p>
                </div>
              </li>
            ))}
          </ul>

          <p className="relative mt-10 text-xs text-white/55">
            Built for people who want meaningful professional connections.
          </p>
        </aside>

        <section
          className={cn(
            "flex flex-1 flex-col bg-card",
            "px-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-6",
            "sm:justify-center sm:px-10 sm:py-10",
          )}
        >
          <div className="mx-auto w-full max-w-md flex-1 sm:flex-none">{children}</div>
        </section>
      </div>
    </main>
  );
}
