/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./pages/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
    theme: {
      extend: {
        fontFamily: {
          sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial'],
        },
        colors: {
          brand: {
            50:  "#eef7ff",
            100: "#d9ecff",
            200: "#bcdcff",
            300: "#8cc3ff",
            400: "#59a6ff",
            500: "#2a86ff",
            600: "#196af4",
            700: "#1456cc",
            800: "#1248a6",
            900: "#123f8a",
          },
        },
      },
    },
    plugins: [],
  }