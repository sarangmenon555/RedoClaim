"use client";
import { useLanguageStore } from "@/store/language";
import { t as translate } from "./strings";

// Usage: const t = useT(); ... {t("nav_overview")}
export function useT() {
  const language = useLanguageStore((s) => s.language);
  return (key: string) => translate(key, language);
}
