"use client";

import {
  Bell,
  Download,
  Globe,
  Lock,
  Palette,
  Shield,
  Trash2,
  User,
  UserCircle,
  UserX,
} from "lucide-react";

import { SettingsItem } from "@/components/settings/SettingsItem";
import type { SettingsSectionId } from "@/stores/settingsStore";

type NavItem = {
  id: SettingsSectionId;
  title: string;
  description: string;
  icon: typeof User;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

const GROUPS: NavGroup[] = [
  {
    label: "Profile & Account",
    items: [
      {
        id: "profile",
        title: "Edit Profile",
        description:
          "Update your profile photo, bio, headline and personal information.",
        icon: UserCircle,
      },
      {
        id: "account",
        title: "Account Information",
        description: "Manage your email, username and account details.",
        icon: User,
      },
    ],
  },
  {
    label: "Privacy & Safety",
    items: [
      {
        id: "privacy",
        title: "Privacy Settings",
        description: "Control who can view your profile, posts and connections.",
        icon: Shield,
      },
      {
        id: "blocked",
        title: "Blocked Users",
        description: "Manage users you have blocked.",
        icon: UserX,
      },
      {
        id: "security",
        title: "Security",
        description: "Manage password and account security.",
        icon: Lock,
      },
    ],
  },
  {
    label: "Notifications",
    items: [
      {
        id: "notifications",
        title: "Notification Preferences",
        description: "Choose what notifications you receive.",
        icon: Bell,
      },
    ],
  },
  {
    label: "Preferences",
    items: [
      {
        id: "appearance",
        title: "Appearance",
        description: "Manage theme and display preferences.",
        icon: Palette,
      },
      {
        id: "language",
        title: "Language",
        description: "Choose your preferred language.",
        icon: Globe,
      },
    ],
  },
  {
    label: "Data & Account",
    items: [
      {
        id: "download",
        title: "Download Your Data",
        description: "Request a copy of your LinkMe information.",
        icon: Download,
      },
      {
        id: "delete",
        title: "Delete Account",
        description: "Deactivate or permanently remove your account.",
        icon: Trash2,
      },
    ],
  },
];

type SettingsSidebarProps = {
  activeSection: SettingsSectionId;
  onSelect: (section: SettingsSectionId) => void;
};

export function SettingsSidebar({ activeSection, onSelect }: SettingsSidebarProps) {
  return (
    <nav className="space-y-6" aria-label="Settings categories">
      {GROUPS.map((group) => (
        <div key={group.label}>
          <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {group.label}
          </p>
          <ul className="space-y-1.5">
            {group.items.map((item) => (
              <li key={item.id}>
                <SettingsItem
                  icon={item.icon}
                  title={item.title}
                  description={item.description}
                  active={activeSection === item.id}
                  onClick={() => onSelect(item.id)}
                />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export { GROUPS as SETTINGS_NAV_GROUPS };
