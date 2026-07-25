"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import {
  Home,
  LogIn,
  MessageCircle,
  Moon,
  PenSquare,
  Search,
  Settings,
  Sun,
  UserPlus,
  UserRound,
  Users,
} from "lucide-react";
import { useTheme } from "next-themes";

import { NotificationBell } from "@/components/notifications/NotificationBell";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";
import { useNotificationStore } from "@/stores/notificationStore";

type NavLink = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const publicLinks: NavLink[] = [
  { href: "/", label: "Home", icon: Home },
  { href: "/search/users", label: "Search", icon: Search },
  { href: "/login", label: "Log in", icon: LogIn },
  { href: "/signup", label: "Sign up", icon: UserPlus },
];

const protectedLinks: NavLink[] = [
  { href: "/home", label: "Feed", icon: Home },
  { href: "/search/users", label: "Search", icon: Search },
  { href: "/create", label: "Post", icon: PenSquare },
  { href: "/network", label: "Network", icon: Users },
  { href: "/messages", label: "Messages", icon: MessageCircle },
  { href: "/profile", label: "Profile", icon: UserRound },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { resolvedTheme, setTheme } = useTheme();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);
  const resetNotifications = useNotificationStore((s) => s.reset);
  const links = isAuthenticated ? protectedLinks : publicLinks;

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between gap-3 px-4">
        <Link
          href={isAuthenticated ? "/home" : "/"}
          className="shrink-0 font-[family-name:var(--font-fraunces)] text-xl font-semibold tracking-tight"
        >
          LinkMe
        </Link>
        <nav className="hidden min-w-0 flex-1 items-center justify-center gap-0.5 md:flex lg:gap-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive =
              pathname === link.href ||
              (link.href !== "/" && pathname.startsWith(`${link.href}/`));
            return (
              <Link
                key={`${link.href}-${link.label}`}
                href={link.href}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground lg:px-3",
                  isActive && "bg-primary/10 font-medium text-primary",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="flex shrink-0 items-center gap-1">
          <NotificationBell />
          {isAuthenticated ? (
            <Button
              variant="ghost"
              size="sm"
              className="hidden md:inline-flex"
              onClick={async () => {
                resetNotifications();
                await logout();
                router.push("/login");
              }}
            >
              Log out
            </Button>
          ) : null}
          <Button
            variant="ghost"
            size="icon"
            aria-label="Toggle theme"
            onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
          >
            <Sun className="h-4 w-4 dark:hidden" />
            <Moon className="hidden h-4 w-4 dark:block" />
          </Button>
        </div>
      </div>
    </header>
  );
}
