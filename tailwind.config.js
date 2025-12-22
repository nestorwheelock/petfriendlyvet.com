/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E8F0F8',
          100: '#D1E1F1',
          200: '#A3C3E3',
          300: '#75A5D5',
          400: '#4787C7',
          500: '#1E4D8C',  // Primary Blue
          600: '#183D70',
          700: '#122E54',
          800: '#0C1E38',
          900: '#060F1C',
        },
        secondary: {
          50: '#EFF8E8',
          100: '#DFF1D1',
          200: '#BFE3A3',
          300: '#9FD575',
          400: '#7FC747',
          500: '#5FAD41',  // Secondary Green
          600: '#4C8A34',
          700: '#396827',
          800: '#26451A',
          900: '#13230D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
