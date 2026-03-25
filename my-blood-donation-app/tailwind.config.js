/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#B22222',
          light: '#D32F2F',
          dark: '#8B0000',
        },
        background: '#F9FAFB',
      }
    },
  },
  plugins: [],
}
