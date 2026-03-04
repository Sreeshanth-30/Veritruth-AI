/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // VeriTruth brand palette
        brand: {
          primary: "#00d2ff",
          secondary: "#7b2ff7",
          accent: "#00e5a0",
          danger: "#ff3a5c",
          warning: "#ffb830",
        },
        dark: {
          50: "#f0f0f5",
          100: "#d1d1e0",
          200: "#a3a3c2",
          300: "#7575a3",
          400: "#4a4a7a",
          500: "#2a2a4a",
          600: "#1e1e3a",
          700: "#16162d",
          800: "#0f0f20",
          900: "#0a0a18",
          950: "#050510",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Space Grotesk", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        "scale-in": "scaleIn 0.3s ease-out",
        float: "float 6s ease-in-out infinite",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-x": "gradientX 15s ease infinite",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        gradientX: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(0,210,255,0.2)" },
          "100%": { boxShadow: "0 0 20px rgba(0,210,255,0.6)" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-gradient":
          "linear-gradient(135deg, #0a0a18 0%, #16162d 50%, #0a0a18 100%)",
      },
      boxShadow: {
        glow: "0 0 15px rgba(0,210,255,0.3)",
        "glow-lg": "0 0 30px rgba(0,210,255,0.4)",
        card: "0 10px 40px rgba(0,0,0,0.3)",
      },
    },
  },
  plugins: [],
};
