// Language codes RedoClaim supports across the app — kept in sync with
// backend SUPPORTED_LANGUAGES in app/services/language/sarvam_service.py

export type LanguageCode = "en" | "hi" | "ml" | "ta" | "te" | "kn";

export interface LanguageInfo {
  code: LanguageCode;
  label: string;      // native-script label, shown in the switcher
  englishName: string;
}

export const SUPPORTED_LANGUAGES: LanguageInfo[] = [
  { code: "en", label: "English",              englishName: "English" },
  { code: "hi", label: "हिन्दी",                englishName: "Hindi" },
  { code: "ml", label: "മലയാളം",                englishName: "Malayalam" },
  { code: "ta", label: "தமிழ்",                 englishName: "Tamil" },
  { code: "te", label: "తెలుగు",                englishName: "Telugu" },
  { code: "kn", label: "ಕನ್ನಡ",                 englishName: "Kannada" },
];

export const DEFAULT_LANGUAGE: LanguageCode = "en";

export function isSupportedLanguage(value: string | null | undefined): value is LanguageCode {
  return !!value && SUPPORTED_LANGUAGES.some((l) => l.code === value);
}

export function getLanguageInfo(code: string | null | undefined): LanguageInfo {
  return SUPPORTED_LANGUAGES.find((l) => l.code === code) || SUPPORTED_LANGUAGES[0];
}
