/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        engaged: '#22c55e',
        neutral: '#eab308',
        disengaged: '#ef4444',
      },
    },
  },
  plugins: [],
};
