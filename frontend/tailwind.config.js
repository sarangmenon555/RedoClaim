/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Core surfaces (near-black, not pure black)
        surface: {
          DEFAULT: "#0A0A0F",   // page background
          1:       "#111118",   // card base
          2:       "#16161F",   // elevated card
          3:       "#1C1C28",   // hover / input bg
          4:       "#232333",   // borders
          5:       "#2E2E42",   // subtle borders
        },

        // ── Primary — electric violet
        violet: {
          50:  "#F3EEFF",
          100: "#E4D4FF",
          200: "#C9A9FF",
          300: "#A97EFF",
          400: "#8B5CF6",
          500: "#7C3AED",
          600: "#6D28D9",
          700: "#5B21B6",
          glow: "#8B5CF6",
        },

        // ── Accent — electric cyan (for highlights)
        cyan: {
          300: "#67E8F9",
          400: "#22D3EE",
          500: "#06B6D4",
          glow: "#22D3EE",
        },

        // ── Accent 2 — neon green (for success/valid)
        neon: {
          300: "#86EFAC",
          400: "#4ADE80",
          500: "#22C55E",
          glow: "#4ADE80",
        },

        // ── Amber — warnings/disclaimers
        amber: {
          300: "#FCD34D",
          400: "#FBBF24",
          500: "#F59E0B",
          600: "#D97706",
        },

        // ── Red — violations/danger
        red: {
          300: "#FCA5A5",
          400: "#F87171",
          500: "#EF4444",
          600: "#DC2626",
          900: "#7F1D1D",
        },

        // ── Text hierarchy
        text: {
          primary:   "#F1F0FF",   // near-white with slight violet tint
          secondary: "#A09CC0",   // muted purple-grey
          tertiary:  "#6B6880",   // very muted
          disabled:  "#3D3B52",
        },
      },

      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },

      borderRadius: {
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
      },

      boxShadow: {
        "glow-violet": "0 0 20px rgba(139, 92, 246, 0.35)",
        "glow-cyan":   "0 0 20px rgba(34, 211, 238, 0.3)",
        "glow-neon":   "0 0 20px rgba(74, 222, 128, 0.3)",
        "card":        "0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
        "card-hover":  "0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(139,92,246,0.2)",
      },

      backgroundImage: {
        "gradient-violet": "linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%)",
        "gradient-hero":   "linear-gradient(135deg, #0A0A0F 0%, #111128 50%, #0A0A0F 100%)",
        "gradient-card":   "linear-gradient(145deg, #16161F 0%, #111118 100%)",
        "grid-pattern":    "radial-gradient(circle, #2E2E42 1px, transparent 1px)",
      },

      animation: {
        "fade-in":    "fadeIn 0.3s ease-in-out",
        "slide-up":   "slideUp 0.3s ease-out",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
        "shimmer":    "shimmer 2s infinite",
      },

      keyframes: {
        fadeIn:    { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp:   { "0%": { transform: "translateY(12px)", opacity: "0" }, "100%": { transform: "translateY(0)", opacity: "1" } },
        glowPulse: { "0%,100%": { boxShadow: "0 0 12px rgba(139,92,246,0.4)" }, "50%": { boxShadow: "0 0 28px rgba(139,92,246,0.7)" } },
        shimmer:   { "0%": { backgroundPosition: "-1000px 0" }, "100%": { backgroundPosition: "1000px 0" } },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
