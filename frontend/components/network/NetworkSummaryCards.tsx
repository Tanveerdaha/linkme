"use client";

import Link from "next/link";
import { Search, Sparkles, UserPlus, Users } from "lucide-react";

import type { NetworkSummary } from "@/services/network";
import { cn } from "@/lib/utils";

type NetworkSummaryCardsProps = {
  summary?: NetworkSummary | null;
  onViewRequests?: () => void;
  onViewSuggestions?: () => void;
  className?: string;
};

export function NetworkSummaryCards({
  summary,
  onViewRequests,
  onViewSuggestions,
  className,
}: NetworkSummaryCardsProps) {
  const cards = [
    {
      key: "connections",
      label: "My Connections",
      count: summary?.connections ?? 0,
      cta: "View connections",
      ctaMobile: "View",
      icon: Users,
      href: "/network/connections",
      onClick: undefined as (() => void) | undefined,
    },
    {
      key: "requests",
      label: "Requests",
      count: summary?.requests_received ?? 0,
      cta: "View requests",
      ctaMobile: "View",
      icon: UserPlus,
      href: undefined as string | undefined,
      onClick: onViewRequests,
    },
    {
      key: "suggestions",
      label: "Suggestions",
      count: summary?.suggestions ?? 0,
      cta: "View suggestions",
      ctaMobile: "View",
      icon: Sparkles,
      href: undefined as string | undefined,
      onClick: onViewSuggestions,
    },
    {
      key: "find",
      label: "Find People",
      count: null as number | null,
      subtitle: "Search and connect with people",
      cta: "Start searching",
      ctaMobile: "Search",
      icon: Search,
      href: "/search/users",
      onClick: undefined as (() => void) | undefined,
    },
  ];

  return (
    <div
      className={cn(
        // Mobile: 2-col compact grid. sm+: existing 2-col, xl: 4-col desktop.
        "grid grid-cols-2 gap-2 sm:gap-3 sm:grid-cols-2 xl:grid-cols-4",
        className,
      )}
    >
      {cards.map((card) => {
        const Icon = card.icon;
        const content = (
          <>
            <div className="flex items-start justify-between gap-2 sm:gap-3">
              <div className="min-w-0">
                <p className="text-xs leading-snug text-muted-foreground sm:text-sm">
                  {card.label}
                </p>
                {typeof card.count === "number" ? (
                  <p className="mt-1 font-[family-name:var(--font-fraunces)] text-2xl font-semibold tabular-nums tracking-tight sm:text-3xl">
                    {card.count}
                  </p>
                ) : (
                  <p className="mt-1.5 hidden text-sm font-medium text-foreground sm:mt-2 sm:block">
                    {card.subtitle}
                  </p>
                )}
              </div>
              <span className="shrink-0 rounded-lg bg-secondary p-2 text-secondary-foreground sm:rounded-xl sm:p-2.5">
                <Icon className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden />
              </span>
            </div>
            <p className="mt-2 text-xs font-medium text-primary sm:mt-4 sm:text-sm">
              <span className="sm:hidden">{card.ctaMobile}</span>
              <span className="hidden sm:inline">{card.cta}</span>
            </p>
          </>
        );

        const classNameCard = cn(
          "rounded-xl border border-border/70 bg-card text-left shadow-sm transition-colors hover:bg-muted/20",
          "p-3 sm:p-5",
        );

        if (card.href) {
          return (
            <Link key={card.key} href={card.href} className={classNameCard}>
              {content}
            </Link>
          );
        }

        return (
          <button
            key={card.key}
            type="button"
            onClick={card.onClick}
            className={classNameCard}
          >
            {content}
          </button>
        );
      })}
    </div>
  );
}
