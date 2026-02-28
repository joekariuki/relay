import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        relay: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
        },
      },
      animation: {
        "spin-slow": "spin 3s linear infinite",
      },
      typography: {
        chat: {
          css: {
            "--tw-prose-body": "#1f2937",
            "--tw-prose-headings": "#111827",
            "--tw-prose-links": "#059669",
            "--tw-prose-bold": "#111827",
            "--tw-prose-code": "#059669",
            "--tw-prose-pre-bg": "#f3f4f6",
            fontSize: "0.875rem",
            lineHeight: "1.625",
            p: {
              marginTop: "0.25em",
              marginBottom: "0.25em",
            },
            "ul, ol": {
              marginTop: "0.25em",
              marginBottom: "0.25em",
            },
            li: {
              marginTop: "0.125em",
              marginBottom: "0.125em",
            },
            h1: { fontSize: "1.125rem" },
            h2: { fontSize: "1rem" },
            h3: { fontSize: "0.9375rem" },
            table: {
              fontSize: "0.8125rem",
            },
            "code::before": { content: "none" },
            "code::after": { content: "none" },
            code: {
              backgroundColor: "#f3f4f6",
              padding: "0.125rem 0.25rem",
              borderRadius: "0.25rem",
              fontWeight: "400",
            },
            pre: {
              borderRadius: "0.5rem",
              padding: "0.75rem",
            },
          },
        },
      },
    },
  },
  plugins: [typography],
};
