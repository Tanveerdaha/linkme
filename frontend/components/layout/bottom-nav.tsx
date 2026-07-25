"use client";

import Link from "next/link";
import { Home, MessageCircle, PenSquare, Search, UserRound, Users } from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";

const guestItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/search/users", label: "Search", icon: Search },
  { href: "/login", label: "Log in", icon: UserRound },
];

const authItems = [
  { href: "/home", label: "Feed", icon: Home },
  { href: "/network", label: "Network", icon: Users },
  { href: "/create", label: "Post", icon: PenSquare },
  { href: "/messages", label: "Messages", icon: MessageCircle },
  { href: "/profile", label: "Profile", icon: UserRound },
];

export function BottomNav({ active }: { active?: string }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const visible = isAuthenticated ? authItems : guestItems;

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-border/70 bg-background/90 backdrop-blur-md md:hidden">
      <ul className="mx-auto flex h-14 max-w-lg items-center justify-around px-2">
        {visible.map((item) => {
          const Icon = item.icon;
          const isActive =
            active === item.href ||
            (item.href !== "/" && Boolean(active?.startsWith(`${item.href}/`)));
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "relative flex flex-col items-center gap-0.5 px-2 text-[10px] text-muted-foreground",
                  isActive && "text-primary",
                )}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
