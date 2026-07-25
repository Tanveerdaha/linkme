"use client";

import Link from "next/link";

import { Feed } from "@/components/feed/Feed";
import { LoginCard } from "@/components/feed/LoginCard";
import { BottomNav } from "@/components/layout/bottom-nav";
import { SiteHeader } from "@/components/layout/site-header";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/authStore";

function SidebarPlaceholders() {
  return (
    <>
      <section className="rounded-2xl border border-border/60 bg-card/60 p-4">
        <h2 className="text-sm font-semibold tracking-tight">Trending</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Topic trends arrive in a later phase. For now, explore the public feed.
        </p>
      </section>
      <section className="rounded-2xl border border-border/60 bg-card/60 p-4">
        <h2 className="text-sm font-semibold tracking-tight">Suggested people</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Connection suggestions will appear here once networking ships.
        </p>
      </section>
    </>
  );
}

export default function PublicHomePage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const hasHydrated = useAuthStore((s) => s._hasHydrated);

  return (
    <div className="relative min-h-screen pb-16 md:pb-0">
      <div
        aria-hidden
        className="animate-soft-pulse pointer-events-none absolute inset-x-0 top-0 h-[42vh] bg-[radial-gradient(ellipse_at_top,color-mix(in_oklab,var(--primary)_18%,transparent),transparent_70%)]"
      />
      <SiteHeader />
      <main className="relative mx-auto grid w-full max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[240px_minmax(0,1fr)_260px] lg:gap-8">
        <aside className="hidden space-y-4 lg:block">
          {!hasHydrated ? (
            <div className="h-48 animate-pulse rounded-2xl bg-muted/50" />
          ) : isAuthenticated ? (
            <section className="animate-fade-up rounded-2xl border border-border/70 bg-card/85 p-5">
              <p className="font-[family-name:var(--font-fraunces)] text-2xl font-semibold tracking-tight">
                LinkMe
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Signed in as @{user?.username}
              </p>
              <div className="mt-4 flex flex-col gap-2">
                <Button asChild>
                  <Link href="/create">Create a post</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/home">Open your feed</Link>
                </Button>
              </div>
            </section>
          ) : (
            <LoginCard />
          )}
          <div className="space-y-4 opacity-90">
            <SidebarPlaceholders />
          </div>
        </aside>

        <section className="min-w-0">
          <div className="mb-4 animate-fade-up">
            <p className="font-[family-name:var(--font-fraunces)] text-3xl font-semibold tracking-tight sm:text-4xl">
              LinkMe
            </p>
            <p className="mt-1 text-sm text-muted-foreground sm:text-base">
              Public posts from the community — browse freely, join to share yours.
            </p>
          </div>
          {!isAuthenticated && hasHydrated ? (
            <div className="mb-4 lg:hidden">
              <LoginCard />
            </div>
          ) : null}
          <div className="rounded-2xl border border-border/70 bg-card/70 px-2 sm:px-3">
            <Feed mode="public" />
          </div>
        </section>

        <aside className="hidden space-y-4 lg:block">
          <SidebarPlaceholders />
        </aside>
      </main>
      <BottomNav active="/" />
    </div>
  );
}
