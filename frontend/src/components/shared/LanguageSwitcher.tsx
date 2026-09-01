"use client";
import { useState, useRef, useEffect } from "react";
import { Languages, Check } from "lucide-react";
import { useLanguageStore } from "@/store/language";
import { SUPPORTED_LANGUAGES } from "@/lib/i18n/languages";
import { useT } from "@/lib/i18n/useT";
import { useAuthStore } from "@/store/auth";
import { authApi } from "@/lib/api";

interface Props {
  // When true (default), selecting a language also saves it as the
  // signed-in user's preferred_language so it's remembered across devices.
  persistToProfile?: boolean;
  compact?: boolean;
}

export default function LanguageSwitcher({ persistToProfile = true, compact = false }: Props) {
  const { language, setLanguage } = useLanguageStore();
  const { isAuthenticated } = useAuthStore();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const t = useT();

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const current = SUPPORTED_LANGUAGES.find((l) => l.code === language) || SUPPORTED_LANGUAGES[0];

  const handleSelect = async (code: string) => {
    setLanguage(code);
    setOpen(false);
    if (persistToProfile && isAuthenticated) {
      try {
        await authApi.updateProfile({ preferred_language: code });
      } catch {
        // Non-critical — language still applies locally via the store.
      }
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        title={t("language_label")}
        className="flex items-center gap-1.5 h-9 px-2.5 rounded-lg text-xs font-medium transition"
        style={{ border: "1px solid var(--surface-5)", color: "var(--text-secondary)" }}
        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "var(--surface-2)")}
        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "transparent")}
      >
        <Languages size={14} />
        {!compact && <span>{current.label}</span>}
      </button>

      {open && (
        <div
          className="absolute right-0 mt-2 w-48 rounded-lg overflow-hidden z-50 animate-fade-in"
          style={{ background: "var(--surface-1)", border: "1px solid var(--surface-4)", boxShadow: "0 8px 30px rgba(0,0,0,0.4)" }}
        >
          <div className="px-3 py-2 text-xs font-semibold tracking-wide uppercase" style={{ color: "var(--text-tertiary)", borderBottom: "1px solid var(--surface-4)" }}>
            {t("language_label")}
          </div>
          {SUPPORTED_LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => handleSelect(l.code)}
              className="w-full flex items-center justify-between px-3 py-2 text-sm transition"
              style={{ color: l.code === language ? "#C4B5FD" : "var(--text-secondary)" }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "var(--surface-2)")}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "transparent")}
            >
              <span>
                {l.label}
                {l.code !== "en" && <span className="ml-1.5 text-xs opacity-50">({l.englishName})</span>}
              </span>
              {l.code === language && <Check size={13} />}
            </button>
          ))}
          <div className="px-3 py-2 text-xs" style={{ color: "var(--text-tertiary)", borderTop: "1px solid var(--surface-4)" }}>
            {t("report_language_note")}
          </div>
        </div>
      )}
    </div>
  );
}
