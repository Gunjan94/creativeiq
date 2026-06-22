/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // CSS-variable driven (see theme.ts applyTheme) so utilities follow the
        // active light/dark palette. <alpha-value> keeps opacity modifiers (bg-ink/80) working.
        sand: "rgb(var(--sand-rgb) / <alpha-value>)",
        offwhite: "rgb(var(--offwhite-rgb) / <alpha-value>)",
        panel: "rgb(var(--panel-rgb) / <alpha-value>)",
        panel2: "rgb(var(--panel2-rgb) / <alpha-value>)",
        line: "rgb(var(--line-rgb) / <alpha-value>)",
        teal: {
          DEFAULT: "rgb(var(--teal-rgb) / <alpha-value>)",
          deep: "rgb(var(--tealDeep-rgb) / <alpha-value>)",
        },
        terracotta: "rgb(var(--terracotta-rgb) / <alpha-value>)",
        ink: "rgb(var(--ink-rgb) / <alpha-value>)",
        stone: "rgb(var(--stone-rgb) / <alpha-value>)",
      },
      fontFamily: {
        serif: ["Georgia", "Cambria", "serif"],
        sans: ["Helvetica Neue", "Arial", "sans-serif"],
      },
      boxShadow: {
        card: "var(--card-shadow, 0 10px 40px -12px rgba(43,43,40,0.25))",
      },
    },
  },
  plugins: [],
};
