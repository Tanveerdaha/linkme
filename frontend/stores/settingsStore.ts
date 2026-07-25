import { create } from "zustand";

export type SettingsSectionId =
  | "profile"
  | "account"
  | "privacy"
  | "blocked"
  | "security"
  | "notifications"
  | "appearance"
  | "language"
  | "download"
  | "delete";

type SettingsState = {
  activeSection: SettingsSectionId;
  loading: boolean;
  setActiveSection: (section: SettingsSectionId) => void;
  setLoading: (loading: boolean) => void;
  /** Placeholder for future preference persistence. */
  updateSettings: (patch: Partial<{ activeSection: SettingsSectionId }>) => void;
};

export const SETTINGS_SECTIONS: SettingsSectionId[] = [
  "profile",
  "account",
  "privacy",
  "blocked",
  "security",
  "notifications",
  "appearance",
  "language",
  "download",
  "delete",
];

export function isSettingsSectionId(value: string | null | undefined): value is SettingsSectionId {
  return Boolean(value && SETTINGS_SECTIONS.includes(value as SettingsSectionId));
}

export const useSettingsStore = create<SettingsState>((set) => ({
  activeSection: "profile",
  loading: false,
  setActiveSection: (section) => set({ activeSection: section }),
  setLoading: (loading) => set({ loading }),
  updateSettings: (patch) => {
    if (patch.activeSection) {
      set({ activeSection: patch.activeSection });
    }
  },
}));
