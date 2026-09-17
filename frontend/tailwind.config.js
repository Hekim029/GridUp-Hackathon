/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
      colors: {
        ink: "#07111f",
        panel: "#0d1b2e",
        cyan: "#2dd4bf",
        amber: "#f59e0b"
      }
    }
  },
  plugins: []
};

