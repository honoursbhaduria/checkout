/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        chassis: "#e0e5ec",
        panel: "#f0f2f5",
        recessed: "#d1d9e6",
        ink: "#2d3436",
        inkMuted: "#4a5568",
        safety: "#ff4757",
        borderShadow: "#babecc",
        borderHighlight: "#ffffff",
        borderDark: "#a3b1c6",
        crtGreen: "#10b981",
        crtAmber: "#f59e0b",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "16px",
        xl: "24px",
        "2xl": "32px",
      },
      boxShadow: {
        card: "8px 8px 16px #babecc, -8px -8px 16px #ffffff",
        floating: "12px 12px 24px #babecc, -12px -12px 24px #ffffff, inset 1px 1px 0 rgba(255,255,255,0.6)",
        pressed: "inset 6px 6px 12px #babecc, inset -6px -6px 12px #ffffff",
        recessed: "inset 4px 4px 8px #babecc, inset -4px -4px 8px #ffffff",
        sharp: "4px 4px 8px rgba(0,0,0,0.15), -1px -1px 1px rgba(255,255,255,0.8)",
        safety: "4px 4px 10px rgba(255, 71, 87, 0.4), -4px -4px 10px rgba(255, 255, 255, 0.7)",
        safetyPressed: "inset 3px 3px 6px rgba(180, 20, 30, 0.6), inset -3px -3px 6px rgba(255, 120, 130, 0.6)",
        ledGreen: "0 0 10px 2px rgba(34, 197, 94, 0.8)",
        ledRed: "0 0 10px 2px rgba(255, 71, 87, 0.8)",
        ledAmber: "0 0 10px 2px rgba(245, 158, 11, 0.8)",
      }
    },
  },
  plugins: [],
}
