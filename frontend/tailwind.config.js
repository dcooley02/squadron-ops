/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Status colors aligned with naval aviation conventions
        fmc: '#22c55e',      // green for Fully Mission Capable
        pmc: '#eab308',      // yellow for Partially Mission Capable
        nmc: '#ef4444',      // red for Non-Mission Capable
      },
    },
  },
  plugins: [],
}