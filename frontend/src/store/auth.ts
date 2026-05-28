import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, tokens: { access_token: string; refresh_token: string }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setAuth: (user, tokens) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);
        }
        set({
          user,
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isAuthenticated: true,
        });
      },

      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
      },
    }),
    {
      name: "redoclaim-auth",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
