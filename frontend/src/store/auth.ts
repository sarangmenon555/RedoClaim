import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import { useLanguageStore } from "@/store/language";
import { isSupportedLanguage } from "@/lib/i18n/languages";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, tokens: { access_token: string }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,

      setAuth: (user, tokens) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", tokens.access_token);
          // The refresh token is no longer handled here at all — the
          // backend sets it as an httpOnly cookie, so it's never visible
          // to this (or any other) JS running on the page.
          localStorage.removeItem("refresh_token"); // clean up any old value
        }
        // Adopt the user's saved report language (set in Settings) so the
        // UI and audit reports switch to it automatically on login,
        // even on a browser that's never set a local preference before.
        if (isSupportedLanguage(user?.preferred_language)) {
          useLanguageStore.getState().setLanguage(user.preferred_language as string);
        }
        set({
          user,
          accessToken: tokens.access_token,
          isAuthenticated: true,
        });
      },

      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
        set({ user: null, accessToken: null, isAuthenticated: false });
      },
    }),
    {
      name: "redoclaim-auth",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
