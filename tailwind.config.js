/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './**/forms.py', 
  ],
  theme: {
    extend: {
      colors: {
        aurora: {
            500: '#1a237e', // Tu azul corporativo
            600: '#0d47a1',
        }
      }
    },
  },
  plugins: [],
}