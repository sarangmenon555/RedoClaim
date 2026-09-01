import { create } from "zustand";
import { persist } from "zustand/middleware";
import { DEFAULT_LANGUAGE, isSupportedLanguage, type LanguageCode } from "@/lib/i18n/languages";

interface LanguageState {
  language: LanguageCode;
  setLanguage: (lang: string) => void;
}

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set) => ({
      language: DEFAULT_LANGUAGE,
      setLanguage: (lang: string) =>
        set({ language: isSupportedLanguage(lang) ? lang : DEFAULT_LANGUAGE }),
    }),
    {
      name: "redoclaim-language",
    }
  )
);

// Non-hook accessor — used by lib/api.ts request interceptor, which runs
// outside React and can't call hooks.
export function getCurrentLanguage(): LanguageCode {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE;
  return useLanguageStore.getState().language;
}
