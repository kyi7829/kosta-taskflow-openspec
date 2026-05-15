/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./frontend/**/*.html",
    "./frontend/**/*.js",
  ],
  theme: {
    extend: {
      screens: {
        // Default: sm=640, md=768, lg=1024
        // Mobile < 768px, Tablet 768-1024px, Desktop > 1024px
      },
    },
  },
  plugins: [],
};
