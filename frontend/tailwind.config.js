/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0f172a',
        ocean: '#0369a1',
        mint: '#14b8a6',
        danger: '#dc2626',
        warning: '#d97706',
      },
      fontFamily: {
        sans: ['Sora', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
